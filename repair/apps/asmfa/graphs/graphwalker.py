try:
    import graph_tool as gt
    from graph_tool import util, search
    from graph_tool.search import BFSVisitor
except ModuleNotFoundError:
    class BFSVisitor:
        pass
import copy
import numpy as np
from django.db.models import Q

from repair.apps.asmfa.models.flows import FractionFlow
from repair.apps.asmfa.models import Actor


class NodeVisitor(BFSVisitor):

    def __init__(self, name, solution, amount, visited, change):
        self.id = name
        self.solution = solution
        self.amount = amount
        self.visited = visited
        self.change = change

    def discover_vertex(self, u):
        """This is invoked when a vertex is encountered for the first time."""
        pass

    def examine_vertex(self, u):
        """Compute the amount change on each inflow for the vertex

        This function is invoked on a vertex as it is popped from the queue.

        Returns
        -------
        dict
            {edge : change}
        """
        changes = {}
        if u.in_degree() > 0:
            all_in = list(u.in_edges())
            for i, e in enumerate(all_in):
                if not self.visited[e]:
                    e_src = e.source()
                    e_src_out = [e for e in e_src.out_edges()]
                    if len(e_src_out) > 1:
                        # For the case when an inflow edge shares the source vertex
                        self.change[e] = (self.amount[e] / sum(
                            [self.amount[out_f] for out_f in e_src_out])) * self.solution
                    else:
                        self.change[e] = (self.amount[e] / sum([self.amount[in_f] for in_f in all_in])) * self.solution
                    # print(self.id[e.source()], '-->', self.id[e.target()], self.change[e])
                    self.visited[e] = True
        else:
            # print("source node,", u.vp.id)
            pass


def traverse_graph(G, edge, solution, amount, upstream=True):
    """Traverse the graph in a breadth-first-search manner

    Parameters
    ----------
    G : the graph to explore
    edge : the starting edge, normally this is the *solution edge*
    upstream : The direction of traversal. When upstream is True, the graph is explored upstream first, otherwise downstream first.

    Returns
    -------
    Edge ProperyMap (float)
        The signed change on the edges
    """
    # Property map for keeping track of the visited edge. Once an edge has been visited
    # it won't be processed anymore.
    r = (False for x in G.get_edges())
    visited = G.new_edge_property("bool", vals=r)
    change = G.new_edge_property("float", val=0.0)
    # G.edge_properties["change"] = change
    # By default we go upstream first, because 'demand dictates supply'
    if upstream:
        G.set_reversed(True)
    else:
        G.set_reversed(False)
    node = edge.target()
    # We are only interested in the edges that define the solution
    # G.set_edge_filter(include)
    # print("\nTraversing in 1. direction")
    search.bfs_search(G, node, NodeVisitor(G.vp["id"], solution, amount, visited, change))
    if G.is_reversed():
        G.set_reversed(False)
    else:
        G.set_reversed(True)
    # print("\nTraversing in 2. direction")
    search.bfs_search(G, node, NodeVisitor(G.vp["id"], solution, amount, visited, change))
    del visited
    G.set_reversed(False)
    # G.clear_filters()
    return change


class GraphWalker:
    def __init__(self, G):
        self.graph = gt.Graph(G)
        self.edge_mask = self.graph.new_edge_property("bool")

    def shift_flow(self, solution_part, actorflows):
        """Shift the flows if necessary in a SolutionPart"""
        if solution_part.implements_new_flow:
            g = copy.deepcopy(self.graph)
            # get all target actors, either origin or destination
            new_targets = Actor.objects.filter(
                activity=solution_part.new_target_activity)
            targets = []
            # get all target vertices
            for actor in new_targets:
                targets += util.find_vertex(g, g.vp['id'], actor.id)
            
            # change all flows by changing origin/destination and amount
            for flow in actorflows:
                edges = util.find_edge(g, g.ep['id'], flow.id)
                if len(edges) > 1:
                    raise ValueError("FractionFlow.id ", flow.id, " is not unique")
                elif len(edges) == 0:
                    print("Cannot find FractionFlow.id ", flow.id, " in the graph")
                else:
                    edge_del = edges[0]
                    amount_flow = g.ep.amount[edge_del]
                    amount_new = amount_flow / len(targets)
                    for target in targets:
                        if(solution_part.keep_origin):
                            # keeping origin of flow
                            e = g.add_edge(edge_del.source(), target)
                        else:
                            # keeping destination of flow                            
                            e = g.add_edge(target, edge_del.target())
                        g.ep.amount[e] = amount_new
                        g.ep.material[e] = solution_part.implementation_flow_material
                    g.remove_edge(edge_del)
            return g
        else:
            return self.graph
        
    def filter_flows(self, solution_object):
        """Keep only the affected_flows and solution_flows in the graph"""
        if len(solution_object.solution_flows) > 0:
            assert isinstance(solution_object.solution_flows[0], tuple), "Flow must be a tuple of (edge id, material name)"
        elif len(solution_object.affected_flows) > 0:
            assert isinstance(solution_object.affected_flows[0], tuple), "Flow must be a tuple of (edge id, material name)"
        selected_flows = solution_object.affected_flows + solution_object.solution_flows
        for e in self.graph.edges():
            eid = self.graph.ep.id[e]
            mat = self.graph.ep.material[e]
            key = (eid, mat)
            if key in selected_flows:
                self.edge_mask[e] = True
            else:
                self.edge_mask[e] = False
    
    def calculate_solution_part(self, solution_part, actorflows, quantity):
        """Calculate the changes on flows for a solution"""
        g = copy.deepcopy(self.graph)
        
        # store the changes for each actor to sum total in the end
        changes_actors = []

        if solution_part.implements_new_flow:
            # shift actor flows to new origin or target
            # get all target actors, either origin or destination
            new_targets = Actor.objects.filter(
                activity=solution_part.new_target_activity)
            targets = []
            # get all target vertices
            for actor in new_targets:
                targets += util.find_vertex(g, g.vp['id'], actor.id)

            if len(targets) == 0:
                print("Cannot find Actors for the new target activity of the SolutionPart")
            
            # Change all flows by changing origin/destination and amount
            for flow in actorflows:
                edges = util.find_edge(g, g.ep['id'], flow.id)
                if len(edges) > 1:
                    raise ValueError("FractionFlow.id ", flow.id, " is not unique")
                elif len(edges) == 0:
                    print("Cannot find FractionFlow.id ", flow.id, " in the graph")
                else:
                    edge_del = edges[0]
                    amount_flow = g.ep.amount[edge_del]
                    amount_new = amount_flow / len(targets)
                    for target in targets:
                        if(solution_part.keep_origin):
                            # keeping origin of flow
                            e = g.add_edge(edge_del.source(), target)
                        else:
                            # keeping destination of flow
                            e = g.add_edge(target, edge_del.target())
                        g.ep.amount[e] = amount_new
                        g.ep.material[e] = solution_part.implementation_flow_material
                        # set the newflow property; needed for storing the changes to db
                        g.ep.newflow[e] = True
                    g.remove_edge(edge_del)

            # this we need because we work with Actors and not Activities, while the user defines the solution
            # with Activities, thus potentially there many Actor-Actor flows in a single Activity
            for flow in actorflows:
                edges = util.find_edge(g, g.ep['id'], flow.id)
                if len(edges) > 1:
                    raise ValueError("FractionFlow.id ", flow.id, " is not unique")
                elif len(edges) == 0:
                    print("Cannot find FractionFlow.id ", flow.id, " in the graph")
                else:
                    # calculate the new value
                    value = (solution_part.a * implementation_quantity.value + solution_part.b)
                    if solution_part.question.is_absolute:
                        if g.ep.amount[e] < 0:
                            raise ValueError("FractionFlow.amount (id %s) is < 0" % g.ep.id[e])
                        value = value / g.ep.amount[e]

                    changes_actors.append(traverse_graph(g, edge=e,
                                                         solution=value,
                                                         amount=g.ep.amount))

        # we compute the solution for each distinct Actor-Actor flow in the implementation flows and
        # assume that we can just sum the changes of this part to the changes of the previous part
        for e in g.edges():
            g.ep.change[e] = g.ep.change[e] + sum(ch[e] for ch in changes_actors)
        return g
    
    def add_changes_to_amounts(self):
        g = copy.deepcopy(self.graph)
        
        # add the change to the amount
        for e in g.edges():
            g.ep.amount[e] = g.ep.amount[e] + g.ep.change[e]
        # remove the change property
        del g.ep["foo"]
        return g
    
    def calculate_solution(self, solution_in_strategy):
        """Calculate the changes on flows for a solution"""
        g = copy.deepcopy(self.graph)
        
        # create new property to store if the flow is created new
        #r = (False for x in g.get_edges())
        g.ep['newflow'] = g.new_edge_property("bool")
        
        # need to traverse_graph() for each SolutionPart and then sum the changes
        # TODO B: store the changes for each part for testing, but this should be replaces by simply adding the changes from the Actor-Actor flows to the final changes edge property map
        changes_solution = dict()
        solution = solution_in_strategy.solution
        solution_parts = solution.solution_parts.all()
        
        # TODO B: get the solution_parts using SolutionPart model
        for part in solution_parts:
            changes_solution_part = g.new_edge_property("float",val=0.0)
            changes_actors = []
            actors_origin = Actor.objects.filter(
                activity=part.implementation_flow_origin_activity)
            actors_destination = Actor.objects.filter(
                activity=part.implementation_flow_destination_activity)
            actorflows = FractionFlow.objects.filter(
                Q(origin__in=actors_origin.values('id')) &
                Q(destination__in=actors_destination.values('id')),
                material=part.implementation_flow_material)
    
            # get the quantity from implementation_question using the solution_in_strategy
            implementation_quantity = ImplementationQuantity.objects.get(
                question=part.question,
                implementation=solution_in_strategy)
            # TODO: what if actorflows is empty list?
            if part.implements_new_flow:
                edges = util.find_edge(g, g.ep['id'], actorflows[0].id)
                # select first result from search query
                if len(edges) > 0:
                    e = edges[0]
                else:
                    print ("No edge found in graph with id: " + str(actorflows[0].id))
                
                # set the newflow property needed for storing the changes
                g.ep.newflow[e] = True
                
                # calculate the new value
                if part.question.is_absolute:
                    if g.ep.amount[e] < 0:
                        raise ValueError("FractionFlow (id %s) is < 0" % g.ep.id[e])
                    value = (part.a * implementation_quantity.value + part.b) / g.ep.amount[e]
                else:
                    value = part.a * implementation_quantity.value + part.b
    
            # this we need because we work with Actors and not Activities, while the user defines the solution
            # with Activities, thus potentially there many Actor-Actor flows in a single Activity
            for implementation_flow in actorflows:
                edges = util.find_edge(g, g.ep['id'], implementation_flow.id)
                if len(edges) > 0:
                    e = edges[0]                    
                    changes_actors.append(traverse_graph(g, edge=e,
                                                         solution=value,
                                                         amount=g.ep.amount))
                else:
                    # not sure what if no edges are found
                    pass
            # we compute the solution for each distinct Actor-Actor flow in the implementation flows and
            # assume that we can just sum the changes
            for edge in g.edges():
                changes_solution_part[edge] = sum(ch[edge] for ch in changes_actors)
            changes_solution[part.id] = changes_solution_part
        # return the graph itself with the modified amounts
        changes = g.new_edge_property("float", val=0.0)
        g.ep.change = changes
        for e in g.edges():
            g.ep.change[e] = sum(part[e] for id,part in changes_solution.items())
        return g    
import graph_tool as gt
import graph_tool.search
import graph_tool.util
import copy
import numpy as np


class NodeVisitor(gt.search.BFSVisitor):

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

        This is the key function for computing the changes on flows. This function is invoked on a vertex as it is 
        popped from the queue.

        Returns
        -------
        dict
            {edge : change}
        """
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
                        self.change[e] = (self.amount[e] / sum(
                            [self.amount[in_f] for in_f in all_in])) * self.solution
                    self.visited[e] = True
        else:
            # print("source node,", u.vp.id)
            pass

class GraphWalker:
    def __init__(self, G):
        self.graph = gt.Graph(G)
        self.edge_mask = self.graph.new_edge_property("bool")

    def filter_flows(self, solution_object):
        """Keep only the affected_flows and solution.solution_flows in the graph"""
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
        
    def _calculate_solution(self, solution):
        """Calculate the changes on flows for a solution"""
        if isinstance(solution, int):
            solution = float(solution)
        assert isinstance(solution, float)
        g = copy.deepcopy(self.graph)
        for e in g.edges():
            if(g.ep.amount[e] != None):
                g.ep.amount[e] = g.ep.amount[e] * solution
        return g

    def calculate_solution(self, solution, upstream=True):
        """Traverse the graph in a breadth-first-search manner

        Parameters
        ----------
        G : the graph to explore
        solution.solution_flows : the starting edges, normally this is the *solution.solution_flows*
        self.edge_mask : edge propery map (bool) to indicate the edges that are part of the solution definition
        solution : double, the solution
        self.graph.ep.amount : edge property map (double) of the material amounts
        upstream : The direction of traversal. When upstream is True, the graph is explored upstream first, otherwise downstream first.

        Returns
        -------
        Edge ProperyMap (float)
            The signed change on the edges
        """
        # Property map for keeping track of the visited edge. Once an edge has been visited
        # it won't be processed anymore.
        defaults = [(False, 0.0) for x in range(self.graph.num_edges(ignore_filter=True))]
        change_collection = {}

        for solution_edge_nr, edge_tuple in enumerate(solution.solution_flows):
            change_collection[solution_edge_nr] = self.graph.new_edge_property("float", vals=defaults[1])
            visited = self.graph.new_edge_property("bool", vals=defaults[0])
            edge_id, edge_material = edge_tuple
            edges_same_id = gt.util.find_edge(self.graph, self.graph.ep["id"], edge_id)
            edge_list = [e for e in edges_same_id if self.graph.ep.material[e] == edge_material]
            assert len(edge_list) < 2, "(Edge ID: %s, material:%s) is not unique!" % (edge_id, edge_material)
            assert len(edge_list) == 1, "Could not find (Edge ID: %s, material:%s)" % (edge_id, edge_material)
            edge = edge_list[0]
            # By default we go upstream first, because we assume that 'demand dictates supply'
            if upstream:
                self.graph.set_reversed(True)
            else:
                self.graph.set_reversed(False)
            node = edge.target()
            # We are only interested in the edges that define the solution
            self.graph.set_edge_filter(self.edge_mask)
            # print("\nTraversing in 1. direction")
            gt.search.bfs_search(self.graph, node, NodeVisitor(self.graph.vp["id"], solution.solution, self.graph.ep.amount, visited,
                                                      change_collection[solution_edge_nr]))
            if self.graph.is_reversed():
                self.graph.set_reversed(False)
            else:
                self.graph.set_reversed(True)
            # print("\nTraversing in 2. direction")
            gt.search.bfs_search(self.graph, node, NodeVisitor(self.graph.vp["id"], solution.solution, self.graph.ep.amount, visited,
                                                      change_collection[solution_edge_nr]))
            del visited
            self.graph.set_reversed(False)
            self.graph.clear_filters()

        g = copy.deepcopy(self.graph)
        for edge in g.edges():
            change = sum([change_collection[solution_edge_nr][edge]
                          for solution_edge_nr, edge_tuple in enumerate(solution.solution_flows)])
            g.ep.amount[edge] = change
        return g
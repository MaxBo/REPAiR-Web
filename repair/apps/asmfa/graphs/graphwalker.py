try:
    import graph_tool as gt
    from graph_tool import search
    from graph_tool.search import BFSVisitor
except ModuleNotFoundError:
    class BFSVisitor:
        pass
import copy
import numpy as np
from django.db.models import Q
import time


class NodeVisitor(BFSVisitor):

    def __init__(self, name, amount, visited, change,
                 balance_factor, fixed, forward=True):
        self.id = name
        self.amount = amount
        self.visited = visited
        self.change = change
        self.balance_factor = balance_factor
        self.fixed = fixed
        self.forward = forward

    def examine_edge(self, e):
        """Compute the amount change on each inflow for the vertex

        This function is invoked on a edge as it is popped from the queue.
        """
        u = e.target()
        vertex_id = int(u)

        balanced_delta = self.change[e] * self.balance_factor[vertex_id]
        edges_out = list(u.out_edges())
        sum_out_f = sum(self.amount[out_f] for out_f in edges_out)
        if sum_out_f:
            amount_factor = balanced_delta / sum_out_f
        elif edges_out:
            amount_factor = balanced_delta / len(edges_out)
        for e_out in edges_out:
            amount_delta = self.amount[e_out] * amount_factor
            if not (self.visited[e_out] and self.visited[e]):
                self.change[e_out] += amount_delta
            elif (abs(self.change[e_out]) < abs(amount_delta)) \
                 and not self.fixed[e_out]:
                self.change[e_out] = amount_delta
            self.visited[e_out] = True

    def examine_vertex(self, u):
        if self.forward:
            return
        vertex_id = int(u)
        edges_in = list(u.in_edges())
        edges_out = list(u.out_edges())
        sum_in_deltas = sum(self.change[in_f] for in_f in edges_in)
        sum_out_deltas = sum(self.change[out_f] for out_f in edges_out)
        delta = sum_in_deltas - sum_out_deltas
        if not delta:
            return
        balanced_delta = delta * self.balance_factor[vertex_id]
        sum_out_f = sum(self.amount[out_f] for out_f in edges_out)
        if sum_out_f:
            amount_factor = balanced_delta / sum_out_f
        elif edges_out:
            amount_factor = balanced_delta / len(edges_out)
        for e_out in edges_out:
            amount_delta = self.amount[e_out] * amount_factor
            if not self.fixed[e_out]:
                self.change[e_out] += amount_delta


def traverse_graph(g, edge, delta, upstream=True):
    """Traverse the graph in a breadth-first-search manner

    Parameters
    ----------
    g : the graph to explore
    edge : the starting edge, normally this is the *solution edge*
    delta : signed change in absolute value (eg. tons) on the implementation flow (delta). For example -26.0 (tons)
    upstream : The direction of traversal. When upstream is True, the graph
               is explored upstream first, otherwise downstream first.

    Returns
    -------
    Edge ProperyMap (float)
        The signed change on the edges
    """
    # Property map for keeping track of the visited edge. Once an edge has
    # been visited it won't be processed anymore.

    amount = g.ep.amount
    #  do we need the "visited"?
    visited = g.new_edge_property("bool", val=False)
    fixed = g.new_edge_property("bool", val=False)
    change = g.new_edge_property("float", val=0.0)
    total_change = g.new_edge_property("float", val=0.0)
    visited[edge] = True
    fixed[edge] = True

    # We are only interested in the edges that define the solution
    g.set_edge_filter(g.ep.include)
    MAX_ITERATIONS = 20
    balance_factor = g.vp.downstream_balance_factor.a
    from repair.apps.asmfa.tests import flowmodeltestdata
    new_delta = delta
    i = 0
    node_visitor = NodeVisitor(g.vp["id"], amount, visited, change,
                               balance_factor, fixed)

    # By default we go upstream first, because 'demand dictates supply'
    if upstream:
        node = reverse_graph(g, node_visitor, edge)
    else:
        node = edge.source()


    # todo:
    # start at the target of the implementation edge, mark
    node_visitor.forward = True
    total_change.a[:] = 0
    while i < MAX_ITERATIONS and abs(new_delta) > 0.00001:
        change.a[:] = 0
        change[edge] = new_delta
        visited.a[:] = False
        visited[edge] = True

        # start in one direction

        search.bfs_search(g, node, node_visitor)

        if i > 0:
            #sum_f = sum(total_change[out_f]+change[out_f]
                        #for out_f in node.out_edges())
            sum_f = node.out_degree(weight=total_change) + \
                node.out_degree(weight=change)
            new_delta = delta - sum_f

        change[edge] = new_delta

        ## Plot changes after forward run
        #g.ep.change.a[:] = change.a
        #flowmodeltestdata.plot_amounts(g,'plastic_deltas.png', 'change')


        # now go downstream, if we started upstream
        # (or upstream, if we started downstream)
        node = reverse_graph(g, node_visitor, edge)
        search.bfs_search(g, node, node_visitor)

        ## Plot changes after backward run
        #g.ep.change.a[:] = change.a
        #flowmodeltestdata.plot_amounts(g,'plastic_deltas.png', 'change')

        # modify the implementation edge only in the first iteration
        if i > 0:
            change[edge] = 0

        # add up the total changes
        total_change.a += change.a

        if node.in_degree():
            sum_f = node.in_degree(weight=total_change)
            #sum_f = sum(total_change[out_f] for out_f in node.in_edges())
            new_delta = delta - sum_f
        else:
            new_delta = 0
        ## Plot total changes
        #g.ep.change.a[:] = total_change.a
        #flowmodeltestdata.plot_amounts(g,f'plastic_deltas_{i}.png', 'change')

        node = reverse_graph(g, node_visitor, edge)
        i += 1



    # finally clean up
    g.set_reversed(False)
    del visited
    g.clear_filters()
    return total_change


def reverse_graph(g, node_visitor: NodeVisitor, edge):
    g.set_reversed(not g.is_reversed())
    node_visitor.balance_factor = 1 / node_visitor.balance_factor
    node = edge.target() if g.is_reversed() else edge.source()
    node_visitor.forward = not node_visitor.forward
    return node


class GraphWalker:
    def __init__(self, g):
        self.graph = gt.Graph(g)

    def calculate(self, implementation_edges, deltas):
        """Calculate the changes on flows for a solution"""
        # ToDo: deepcopy might be expensive. Why do we clone here?
        # NOTE BD: initially the idea was that the this 'calculate' function
        # returns a copy of the graph with the updated amounts. Needed to return
        # an updated copy in order to compare this updated copy with the original
        # graph, so we can say what was changed by the solution.
        # For this, we need a deepcopy, otherwise the original graph would be
        # overwritten.
        # If it is OK to overwrite the amounts on the input graph because we
        # have this data in the database so we can compare the output (right?),
        # then no need to deepcopy.
        g = copy.deepcopy(self.graph)

        # store the changes for each actor to sum total in the end
        overall_changes = None

        for i, edge in enumerate(implementation_edges):

            g.ep.include[edge] = True
            solution_delta = deltas[i]
            changes = traverse_graph(g, edge=edge,
                                     delta=solution_delta)
            if overall_changes is None:
                overall_changes = changes.a
            else:
                overall_changes += changes.a
            g.ep.include[edge] = False

        if overall_changes is not None:
            g.ep.amount.a += overall_changes

            has_changed = overall_changes != 0
            g.ep.changed.a[has_changed] = True

        return g

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
import time

from repair.apps.asmfa.models.flows import FractionFlow
from repair.apps.asmfa.models import Actor


class NodeVisitor(BFSVisitor):

    def __init__(self, name, amount, visited, change, total_change,
                 balance_factor):
        self.id = name
        self.amount = amount
        self.visited = visited
        self.change = change
        self.total_change = total_change
        self.balance_factor = balance_factor

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
            #elif abs(self.change[e_out]) < abs(amount_delta):
                #self.change[e_out] = amount_delta
            self.visited[e_out] = True


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
    visited = g.new_edge_property("bool", val=False)
    change = g.new_edge_property("float", val=0.0)
    total_change = g.new_edge_property("float", val=0.0)
    visited[edge] = True

    # We are only interested in the edges that define the solution
    g.set_edge_filter(g.ep.include)
    MAX_ITERATIONS = 5
    new_delta = delta
    i = 0
    from repair.apps.asmfa.tests import flowmodeltestdata
    while i < MAX_ITERATIONS and abs(new_delta) > 0.001:
        change[edge] = new_delta

        # By default we go upstream first, because 'demand dictates supply'
        if upstream:
            g.set_reversed(True)
            balance_factor = 1 / g.vp.downstream_balance_factor.a
            node = edge.target()
            target_node = edge.source()

        else:
            g.set_reversed(False)
            balance_factor = g.vp.downstream_balance_factor.a
            node = edge.source()
            target_node = edge.target()

        node_visitor = NodeVisitor(g.vp["id"], amount, visited, change,
                                   total_change, balance_factor)
        search.bfs_search(g, node, node_visitor)

        #total_change.a[:] += change.a
        #change.a[:] = 0
        sum_f = sum(change[out_f] for out_f in node.out_edges())
        new_delta = delta - sum_f
        #change[edge] = new_delta

        # now go downstream, if we started upstream
        # (or upstream, if we started downstream)

        g.set_reversed(not g.is_reversed())
        node = edge.target() if g.is_reversed() else edge.source()
        target_node = edge.source() if g.is_reversed() else edge.target()
        # reverse the balancing factors
        node_visitor.balance_factor = 1 / node_visitor.balance_factor

        visited.a[:] = False
        visited[edge] = True
        total_change.a[:] += change.a
        change.a[:] = 0
        change[edge] = new_delta
        g.ep.change.a[:] = total_change.a
        flowmodeltestdata.plot_amounts(g,'plastic_deltas.png', 'change')

        # print("\nTraversing in 2. direction")
        search.bfs_search(g, node, node_visitor)

        sum_f = sum(change[out_f] for out_f in target_node.out_edges())
        new_delta = delta - sum_f

        g.ep.change.a[:] = total_change.a
        flowmodeltestdata.plot_amounts(g,'plastic_deltas.png', 'change')

        total_change.a[:] += change.a
        change.a[:] = 0
        change[edge] = new_delta
        visited.a[:] = False

        g.set_reversed(False)
        i += 1
        total_change[edge] = delta

    # finally clean up
    del visited
    g.clear_filters()
    return node_visitor.total_change


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

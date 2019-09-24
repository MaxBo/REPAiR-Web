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

    def __init__(self, name, solution, amount, visited, change,
                 balance_factor):
        self.id = name
        self.solution = solution
        self.amount = amount
        self.visited = visited
        self.change = change
        self.balance_factor = balance_factor

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
        vertex_id = int(u)
        changes = {}
        if u.in_degree() > 0:
            all_in = list(u.in_edges())
            # ToDo: if all out_edges = 0, distribute equally
            # ToDo: np e.g. g.get_out_edges(node, eprops=[g.ep.amount])
            for i, e in enumerate(all_in):
                if not self.visited[e]:
                    e_src = e.source()
                    e_src_out = list(e_src.out_edges())
                    if len(e_src_out) > 1:
                        # For the case when an inflow edge shares the
                        # source vertex
                        sum_out_f = sum(self.amount[out_f] for out_f in e_src_out)
                        if sum_out_f and self.amount[e]:
                            # (self.amount[e] / sum_out_f) gives a fraction of
                            # how much does the current flow share/contribute to
                            # the total outflow from its source vertex. Thus if
                            # there is only a single flow then this gives 1.
                            self.change[e] = (self.amount[e] / sum_out_f) * self.solution * self.balance_factor[vertex_id]
                        else:
                            # If there are neighbour edges sharing the same source, but their sum is 0, then
                            # revert to compute the ratio from all inflows. However this case might mean that
                            # we are trying to compute something where we don't have enough information yet. Because
                            # the edges exist, but their amount is 0.
                            sum_in_f = sum(self.amount[in_f] for in_f in all_in)
                            if sum_in_f:
                                self.change[e] = (self.amount[e] / sum_in_f) * self.solution * self.balance_factor[vertex_id]
                            else:
                                self.change[e] = self.solution * self.balance_factor[vertex_id]
                    else:
                        sum_in_f = sum(self.amount[in_f] for in_f in all_in)
                        if sum_in_f:
                            self.change[e] = (self.amount[e] / sum_in_f) * self.solution * self.balance_factor[vertex_id]
                        else:
                            self.change[e] = self.solution * self.balance_factor[vertex_id]
                    # print(self.id[e.source()], '-->',
                    # self.id[e.target()], self.change[e])
                    self.visited[e] = True
        else:
            # print("source node,", u.vp.id)
            pass


def traverse_graph(g, edge, solution, upstream=True):
    """Traverse the graph in a breadth-first-search manner

    Parameters
    ----------
    g : the graph to explore
    edge : the starting edge, normally this is the *solution edge*
    solution : signed change in absolute value (eg. tons) on the implementation flow (delta). For example -26.0 (tons)
    upstream : The direction of traversal. When upstream is True, the graph
               is explored upstream first, otherwise downstream first.

    Returns
    -------
    Edge ProperyMap (float)
        The signed change on the edges
    """
    # Property map for keeping track of the visited edge. Once an edge has
    # been visited it won't be processed anymore.
    r = (False for x in g.get_edges())
    amount = g.ep.amount
    visited = g.new_edge_property("bool", vals=r)
    change = g.new_edge_property("float", val=0.0)
    # G.edge_properties["change"] = change
    # By default we go upstream first, because 'demand dictates supply'
    if upstream:
        g.set_reversed(True)
        balance_factor = 1 / g.vp.downstream_balance_factor.a
    else:
        g.set_reversed(False)
        balance_factor = g.vp.downstream_balance_factor.a
    node = edge.target()
    # We are only interested in the edges that define the solution
    g.set_edge_filter(g.ep.include)
    # print("\nTraversing in 1. direction")
    node_visitor = NodeVisitor(g.vp["id"], solution, amount, visited, change,
                               balance_factor)
    search.bfs_search(g, node, node_visitor)
    if g.is_reversed():
        g.set_reversed(False)
    else:
        g.set_reversed(True)
    # reverse the balancing factors
    node_visitor.balance_factor = 1 / node_visitor.balance_factor
    # print("\nTraversing in 2. direction")
    search.bfs_search(g, node, node_visitor)
    del visited
    g.set_reversed(False)
    g.clear_filters()
    return node_visitor.change


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

        # set all changes to zero
        g.ep.change.a[:] = 0

        for i, edge in enumerate(implementation_edges):

            g.ep.include[edge] = True
            start = time.time()
            solution_delta = deltas[i]
            changes = traverse_graph(g, edge=edge,
                                     solution=solution_delta)
            end = time.time()
            print(i, end-start)
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

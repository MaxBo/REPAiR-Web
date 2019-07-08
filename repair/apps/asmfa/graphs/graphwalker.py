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


class Formula:
    def __init__(self, a=1, b=0, q=0, is_absolute=False):
        '''
        linear change calculation

        absolute change:
        v’ = v + delta
        delta = a * q + b

        relative change:
        v’ = v * factor
        factor = a * q + b

        Parameters
        ----------
        a: float, optional
           by default 1
        q: float, optional
           quantity (user input), by default 0
        b: float, optional
           by default 0
        is_absolute: bool, optional
           absolute change, by default False
        '''
        self.a = a
        self.b = b
        self.q = q
        self.is_absolute = is_absolute

    def calculate(self, v):
        '''
        Parameters
        ----------
        v: float,
           value to apply formula to

        Returns
        -------
        v': float
            calculated value
        '''
        return self.calculate_factor(v) * v

    def calculate_factor(self, v=None):
        '''
        Parameters
        ----------
        v: float, optional
           needed for calculation of a

        Returns
        -------
        factor: float
            calculated factor
        '''
        if self.is_absolute:
            if v is None:
                raise ValueError('Value needed for calculation of a factor for '
                                 'absolute changes')
            delta = self.a * self.q + self.b
            v_ = v + delta
            factor = v_ / v
        else:
            factor = self.a * self.q + self.b
        return factor



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
            # ToDo: np e.g. g.get_out_edges(node, eprops=[g.ep.amount])
            for i, e in enumerate(all_in):
                if not self.visited[e]:
                    e_src = e.source()
                    e_src_out = [e for e in e_src.out_edges()]
                    if len(e_src_out) > 1:
                        # For the case when an inflow edge shares the
                        # source vertex
                        self.change[e] = (
                            self.amount[e] / sum(
                                [self.amount[out_f] for out_f in e_src_out])
                            ) * self.solution
                    else:
                        self.change[e] = (
                            self.amount[e] / sum(
                                [self.amount[in_f] for in_f in all_in])
                            ) * self.solution
                    # print(self.id[e.source()], '-->',
                    # self.id[e.target()], self.change[e])
                    self.visited[e] = True
        else:
            # print("source node,", u.vp.id)
            pass


def traverse_graph(g, edge, solution, amount, upstream=True):
    """Traverse the graph in a breadth-first-search manner

    Parameters
    ----------
    g : the graph to explore
    edge : the starting edge, normally this is the *solution edge*
    solution : relative change of implementation flow
               (factor to multiply amount with)
    amount : PropertyMap
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
    visited = g.new_edge_property("bool", vals=r)
    change = g.new_edge_property("float", val=0.0)
    # G.edge_properties["change"] = change
    # By default we go upstream first, because 'demand dictates supply'
    if upstream:
        g.set_reversed(True)
    else:
        g.set_reversed(False)
    node = edge.target()
    # We are only interested in the edges that define the solution
    g.set_edge_filter(g.ep.include)
    # print("\nTraversing in 1. direction")
    search.bfs_search(g, node, NodeVisitor(
        g.vp["id"], solution, amount, visited, change))
    if g.is_reversed():
        g.set_reversed(False)
    else:
        g.set_reversed(True)
    # print("\nTraversing in 2. direction")
    search.bfs_search(g, node, NodeVisitor(
        g.vp["id"], solution, amount, visited, change))
    del visited
    g.set_reversed(False)
    g.clear_filters()
    return change


class GraphWalker:
    def __init__(self, g):
        self.graph = gt.Graph(g)
        self.edge_mask = self.graph.new_edge_property("bool")

    def calculate(self, implementation_edges, formula: Formula):
        """Calculate the changes on flows for a solution"""
        g = copy.deepcopy(self.graph)
        g.ep.change.a[:] = 0

        # store the changes for each actor to sum total in the end
        changes_actors = []
        if formula.is_absolute:
            total = sum(g.ep.amount[edge] for edge in implementation_edges)
            new_total = formula.calculate(total)
            #factor = formula.calculate_factor(total)
        else:
            factor = formula.calculate_factor()

        for i, edge in enumerate(implementation_edges):

            g.ep.include[edge] = True
            start = time.time()
            amount = g.ep.amount[edge]
            if formula.is_absolute:
                # distribute total change to changes on edges
                # depending on share of total
                solution_factor = new_total * amount / total
            else:
                solution_factor = factor
            changes = traverse_graph(g, edge=edge,
                                     solution=solution_factor,
                                     amount=g.ep.amount)
            changes_actors.append(changes)
            self.graph.ep.include[edge] = False
            end = time.time()
            print(f'edge {i} - {end-start}s')

            #if (i > 50):
                #break

        # we compute the solution for each distinct Actor-Actor flow in the
        # implementation flows and assume that we can just sum the changes
        # of this part to the changes of the previous part
        for e in g.edges():
            # ToDo: optimize performance of summing changes (get rid of loops)
            delta = sum(ch[e] for ch in changes_actors)
            g.ep.amount[e] += delta
            if (delta != 0):
                g.ep.changed[e] = True
        return g

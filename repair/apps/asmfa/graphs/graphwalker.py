import graph_tool as gt
import copy
import numpy as np

class GraphWalker:
    def __init__(self, G):
        self.graph = gt.Graph(G)
        self.edge_mask = self.graph.new_edge_property("bool")

    def filter_flows(self, solution_object):
        """Keep only the affected_flows and solution_flows in the graph"""
        for e in self.graph.edges():
            # Eventually, the split edges are going to be identified by (source, target, material) and not ID, because
            # the .id property is duplicated if the edge was split
            eid = self.graph.ep.id[e]
            if eid in solution_object.affected_flows or eid in solution_object.solution_flows:
                self.edge_mask[e] = True
            else:
                self.edge_mask[e] = False
        
    def calculate_solution(self, solution):
        """Calculate the changes on flows for a solution"""
        if isinstance(solution, int):
            solution = float(solution)
        assert isinstance(solution, float)
        g = copy.deepcopy(self.graph)
        for e in g.edges():
            if(g.ep.amount[e] != None):
                g.ep.amount[e] = g.ep.amount[e] * solution
        return g
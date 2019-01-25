import graph_tool as gt
import copy
import numpy as np

class GraphWalker:
    def __init__(self, G):
        self.graph = gt.Graph(G)
        self.edge_mask = self.graph.new_edge_property("bool")

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
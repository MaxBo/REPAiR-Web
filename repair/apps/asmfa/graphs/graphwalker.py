import graph_tool as gt
import copy

class GraphWalker:
    def __init__(self, G):
        self.graph = G
        
    def calculate_solution(self, solution):
        """Calculate the changes on flows for a solution"""
        assert isinstance(solution, float)
        g = copy.deepcopy(self.graph)
        for e in g.edges():
            if(g.ep.flow[e] != None):
                g.ep.flow[e]['amount'] = g.ep.flow[e]['amount'] * solution
        return g
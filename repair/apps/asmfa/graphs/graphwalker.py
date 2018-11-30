import graph_tool as gt

class GraphWalker:
    def __init__(self, G):
        self.graph = G
        
    def calculate_solution(self, solution):
        """Calculate the changes on flows for a solution"""
        assert isinstance(solution, float)
        g = self.graph.copy()
        for e in self.graph.edges():
            if(self.graph.ep.flow[e] != None):
                g.ep.flow[e]['amount'] = self.graph.ep.flow[e]['amount'] * solution
        return g
import graph_tool as gt
import copy
import numpy as np

class GraphWalker:
    def __init__(self, G):
        self.graph = self.split_flows(G)

    def split_flows(self, G):
        """Split the flows based on material composition

        If a flow is composed of different materials, it is split into individual flows per material
        with the corresponding amount.
        If the flow is composed of a single material, the composition property is removed and replaced with material.

        Returns
        -------
        graph
            The updated graph
        eprop_material
            Edge property (materials), string
        eprop_amount
            Edge property (amount), double
        """
        g = copy.deepcopy(G)
        g.clear_edges()
        del g.edge_properties['flow']
        eprops = G.edge_properties.keys()
        amount_list = []
        material_list = []
        assert 'flow' in eprops, "The graph must have 'flow' edge property"
        e_list = []
        for e in G.edges():
            prop = G.ep.flow[e]
            assert isinstance(prop, dict), "Edge property flow must be a dictionary in edge {}".format(e)
            for material, percent in prop['composition'].items():
                e_list.append(np.array([e.source(), e.target()], dtype=int))
                amount_list.append(float(prop['amount']) * float(percent))
                material_list.append(material)
        e_array = np.vstack(e_list)
        g.add_edge_list(e_array)
        eprop_amount = g.new_edge_property("float", vals=amount_list)
        eprop_material = g.new_edge_property("string", vals=material_list)
        g.edge_properties['amount'] = eprop_amount
        g.edge_properties['material'] = eprop_material
        return g
        
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
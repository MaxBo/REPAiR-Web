import graph_tool as gt
import copy
import numpy as np

class GraphWalker:
    def __init__(self, G):
        self.graph = self.split_flows(G)
        self.edge_mask = self.graph.new_edge_property("bool")

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
        eprops = G.edge_properties.keys()
        assert 'flow' in eprops, "The graph must have 'flow' edge property"
        assert 'id' in eprops, "Edges must have an 'id' property"
        del g.edge_properties['flow']
        del g.edge_properties['id']
        amount_list = []
        material_list = []
        eid_list = []
        e_list = []
        for e in G.edges():
            prop = G.ep.flow[e]
            eid = G.ep.id[e]
            assert isinstance(prop, dict), "Edge property flow must be a dictionary in edge {}".format(e)
            for material, percent in prop['composition'].items():
                e_list.append(np.array([e.source(), e.target()], dtype=int))
                amount_list.append(float(prop['amount']) * float(percent))
                material_list.append(material)
                # Yes, split edges are going to have duplicate ID. That's needed so the split edges can be
                # related to the original edges in the DB.
                eid_list.append(eid)
        e_array = np.vstack(e_list)
        g.add_edge_list(e_array)
        eprop_amount = g.new_edge_property("float", vals=amount_list)
        eprop_material = g.new_edge_property("string", vals=material_list)
        eprop_id = g.new_edge_property("int", vals=eid_list)
        g.edge_properties['amount'] = eprop_amount
        g.edge_properties['material'] = eprop_material
        g.edge_properties['id'] = eprop_id
        return g

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
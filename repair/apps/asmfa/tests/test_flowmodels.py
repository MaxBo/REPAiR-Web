# -*- coding: utf-8 -*-

from repair.apps.asmfa.tests.flowmodeltestdata import (
    GenerateTestDataMixin,
    GenerateBigTestDataMixin)
from repair.apps.asmfa.models import Actor, Actor2Actor, ActorStock
from repair.apps.asmfa.graphs.graph import BaseGraph, GraphWalker
from django.test import TestCase
from os import path

from graph_tool import util as gt_util


class GenerateGraphTest(GenerateTestDataMixin, TestCase):
    """
    Test if the graph object is correctly generated
    """
    def setUp(self):
        super().setUp()
        self.create_keyflow()
        self.create_materials()
        self.create_actors()
        self.create_flows()
        self.create_solutions()
        self.graphbase = BaseGraph(self.kic)
        self.graph = self.graphbase.build()
        
    def test_graph_elements(self):
        """Test the Generation of the graph object"""
        # testdata
        assert Actor.objects.count() == 20
        assert Actor2Actor.objects.count() == 30
        assert ActorStock.objects.count() == 2

    def test_graph_creation(self):
        """Test the Generation of the graph object"""
        assert path.isfile(self.graphbase.filename)
        assert self.graph.num_vertices() == Actor.objects.count() - ActorStock.objects.count()
        assert self.graph.num_vertices() == 18
        assert self.graph.num_vertices() == len(self.graph.vp.id.a)
        assert self.graph.num_edges() == 32
        assert self.graph.num_edges() == len(self.graph.ep.id.a)
        for e in self.graph.edges():
            assert len(self.graph.ep.flow[e]['composition']) > 0

    def test_split_flows(self):
        """Test if the flows are split by material and the amounts are updated correctly"""
        gwalker = GraphWalker(self.graph)
        eprops = gwalker.graph.edge_properties.keys()
        assert "amount" in eprops
        assert "material" in eprops
        assert "flow" not in eprops
        assert gwalker.graph.num_vertices() == Actor.objects.count() - ActorStock.objects.count()
        assert gwalker.graph.num_vertices() == len(self.graph.vp.id.a)
        x = gwalker.graph.num_edges()
        assert gwalker.graph.num_edges() == 38
        assert gwalker.graph.num_edges() == len(self.graph.ep.id.a)
        pu = gt_util.find_vertex(gwalker.graph, gwalker.graph.vp['name'], "packaging_utrecht")
        pl = gt_util.find_vertex(gwalker.graph, gwalker.graph.vp['name'], "packaging_leiden")
        ah1 = gt_util.find_vertex(gwalker.graph, gwalker.graph.vp['name'], "ah_den_haag_1")
        ah2 = gt_util.find_vertex(gwalker.graph, gwalker.graph.vp['name'], "ah_den_haag_2")
        ah3 = gt_util.find_vertex(gwalker.graph, gwalker.graph.vp['name'], "ah_den_haag_3")
        for v in [pu, pl, ah1, ah2, ah3]:
            assert len(v) == 1

        pu_ah1 = gwalker.graph.edge(pu[0], ah1[0], all_edges=True)
        assert len(pu_ah1) == 2
        total_amount = sum([gwalker.graph.ep.amount[e] for e in pu_ah1])
        assert (total_amount - 10.0) < 0.001
        mat = []
        for e in pu_ah1:
            mat.append(gwalker.graph.ep.material[e])
            if gwalker.graph.ep.material[e] == "Cucumber":
                cucumber_edge = e
            elif gwalker.graph.ep.material[e] == "Plastic":
                plastic_edge = e
            else:
                self.fail("Unexpected material in flow")
        plastic_amount = gwalker.graph.ep.amount[plastic_edge]
        cucumber_amount = gwalker.graph.ep.amount[cucumber_edge]
        assert abs(plastic_amount - 1.5) < 0.001
        assert abs(cucumber_amount - 8.5) < 0.001

        pu_ah2 = gwalker.graph.edge(pu[0], ah2[0], all_edges=True)
        assert len(pu_ah2) == 2
        mat = []
        for e in pu_ah2:
            mat.append(gwalker.graph.ep.material[e])
            if gwalker.graph.ep.material[e] == "Cucumber":
                cucumber_edge = e
            elif gwalker.graph.ep.material[e] == "Plastic":
                plastic_edge = e
            else:
                self.fail("Unexpected material in flow")
        plastic_amount = gwalker.graph.ep.amount[plastic_edge]
        cucumber_amount = gwalker.graph.ep.amount[cucumber_edge]
        assert abs(plastic_amount - 2.25) < 0.001
        assert abs(cucumber_amount - 12.75) < 0.001

        pu_ah3 = gwalker.graph.edge(pu[0], ah3[0], all_edges=True)
        assert len(pu_ah3) == 2
        mat = []
        for e in pu_ah3:
            mat.append(gwalker.graph.ep.material[e])
            if gwalker.graph.ep.material[e] == "Cucumber":
                cucumber_edge = e
            elif gwalker.graph.ep.material[e] == "Plastic":
                plastic_edge = e
            else:
                self.fail("Unexpected material in flow")
        plastic_amount = gwalker.graph.ep.amount[plastic_edge]
        cucumber_amount = gwalker.graph.ep.amount[cucumber_edge]
        assert abs(plastic_amount - 0.75) < 0.001
        assert abs(cucumber_amount - 4.25) < 0.001

    def test_filter_flows(self):
        """Test if only the affected_flows and solution_flows are kept in the graph"""
        for solution_object in self.solutions:
            gwalker = GraphWalker(self.graph)
            gwalker.filter_flows(solution_object)
            mask = gwalker.edge_mask
            gwalker.graph.set_edge_filter(mask)
            filtered_edges = set(gwalker.graph.ep.id.fa)
            selected_flows = set(solution_object.affected_flows).union(set(solution_object.solution_flows))
            assert len(filtered_edges) == len(selected_flows)
            assert len(selected_flows.difference(filtered_edges)) == 0
            # gwalker.graph.clear_filters()

    def test_graph_calculation(self):
        """Test the calculations using the graph object"""
        gwalker = GraphWalker(self.graph)
        graph2 = gwalker.calculate_solution(2.0)
        assert graph2.num_vertices() == Actor.objects.count() - ActorStock.objects.count()
        assert graph2.num_vertices() == len(self.graph.vp.id.a)
        assert graph2.num_edges() == 38
        assert graph2.num_edges() == len(self.graph.ep.id.a)
        e = next(self.graph.edges())
        assert self.graph.ep.id[e] == graph2.ep.id[e]
        assert self.graph.ep.amount[e] * 2 == graph2.ep.amount[e]
        
    def test_apply_solution(self):
        """Test applying the solutinos to the graph object"""
        gwsolution = GraphWalker(self.graph)
        for s in self.solutions:
            gwsolution.graph = gwsolution.calculate_solution(s.solution)
            
        e = next(gwsolution.graph.edges())
        assert gwsolution.graph.ep.amount[e] == 120

class GenerateBigGraphTest(GenerateBigTestDataMixin, TestCase):
    """
    Test if the graph object is correctly generated
    """
    def setUp(self):
        super().setUp()
        self.create_keyflow()
        self.create_materials()
        self.create_actors(1000)
        self.create_flows(10000)
        self.graphbase = BaseGraph(self.kic)
        self.graph = self.graphbase.build()

    def test_big_graph_elements(self):
        """Test the Generation of the graph object"""
        # testdata
        assert Actor.objects.count() == 1000
        assert Actor2Actor.objects.count() == 10000
        
    def test_big_graph_creation(self):
        """Test the Generation of the graph object"""
        assert path.isfile(self.graphbase.filename)
        assert self.graph.num_vertices() == 1000
        assert self.graph.num_vertices() == len(self.graph.vp.id.a)
        assert self.graph.num_edges() == 10000
        assert self.graph.num_edges() == len(self.graph.ep.id.a)

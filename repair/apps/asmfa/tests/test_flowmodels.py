# -*- coding: utf-8 -*-

'''
from repair.apps.asmfa.tests.flowmodeltestdata import (
    GenerateTestDataMixin,
    GenerateBigTestDataMixin)
from repair.apps.changes.tests.test_strategies import BreadToBeerSolution
from repair.apps.asmfa.models import (
    Actor, Actor2Actor, ActorStock
)
from repair.apps.changes.models.solutions import Solution
from repair.apps.asmfa.graphs.graph import BaseGraph, GraphWalker
from django.test import TestCase
from os import path

from graph_tool import util as gt_util

# B: nice back-and-forth referencing here with BreadToBeerSolution...
# B: this test requires the output of another test
class BreadToBeerTestWalker(BreadToBeerSolution):
    """Bread to Beer case with dummy data"""
    def setUp(self):
        self.graphbase = BaseGraph(self.keyflow)
        self.graph = self.graphbase.build()

    def test_data_setup(self):
        assert "brewery_1" == self.brewery_1.name
        assert "brewery_2" == self.brewery_2.name

    def test_shift_flows(self):
        gwalker = GraphWalker(self.graph)
        solution_object = Solution.objects.filter(name='Bread to Beer')
        shifted_flows = gwalker.shift_flows(solution_object[0],
                            self.bread_to_brewery,
                            self.keyflow)
        # save graph for manual verification
        shifted_flows.save('/home/vagrant/REPAiR-Web/keyflow-2-shifted.gt')
        assert gwalker.graph.num_vertices() == shifted_flows.num_vertices()
        # because now we have two targets (the two breweries) instead of one (incinerator)
        assert gwalker.graph.num_edges() + 100 == shifted_flows.num_edges()
        household0 = gt_util.find_vertex(shifted_flows,
                                         shifted_flows.vp["name"], "household0")[0]
        targets = household0.out_edges()
        bread_targets = [t for t in targets if shifted_flows.ep.material[t] == 'bread']
        assert all(shifted_flows.vp.name[t.target()] != "incinerator Amsterdam" for t in bread_targets)

    def test_graph_calculation(self):
        gwalker = GraphWalker(self.graph)
        solution_object = Solution.objects.filter(name='Bread to Beer')
        gwalker.graph = gwalker.shift_flows(solution_object[0],
                            self.bread_to_brewery,
                            self.keyflow)
        # !!! QUANTITY SHOULD BE PART OF THE ImplementationQuantity model !!!
        implementation_quantity = 0.5
        changes = gwalker.calculate_solution(
            solution=solution_object[0],
            solution_parts=[self.bread_to_brewery],
            quantity=implementation_quantity
        )
        changes.save('/home/vagrant/REPAiR-Web/keyflow-2-changes.gt')
        # graph2 = gwalker.calculate_solution(2.0)
        # assert graph2.num_vertices() == Actor.objects.count() - ActorStock.objects.count()
        # assert graph2.num_vertices() == len(self.graph.vp.id.a)
        # assert graph2.num_edges() == gwalker.graph.num_edges()
        # e = next(self.graph.edges())
        # assert self.graph.ep.id[e] == graph2.ep.id[e]
        # assert self.graph.ep.amount[e] * 2 == graph2.ep.amount[e]

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
        assert self.graph.num_edges() == 38
        assert self.graph.num_edges() == len(self.graph.ep.id.a)
        for e in self.graph.edges():
            assert self.graph.ep.amount[e] > 0

    def test_split_flows(self):
        """Test if the flows are split by material and the amounts are updated correctly"""
        gwalker = GraphWalker(self.graph)
        eprops = gwalker.graph.edge_properties.keys()
        assert "amount" in eprops
        assert "material" in eprops
        assert "flow" not in eprops
        assert gwalker.graph.num_vertices() == Actor.objects.count() - ActorStock.objects.count()
        assert gwalker.graph.num_vertices() == len(self.graph.vp.id.a)
        assert gwalker.graph.num_edges() == 38

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
        assert (total_amount - 1000) < 1
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
        assert plastic_amount == 150
        assert cucumber_amount == 850

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
        assert plastic_amount ==225
        assert cucumber_amount == 1275

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
        assert plastic_amount == 75
        assert cucumber_amount == 425

    def test_filter_flows(self):
        """Test if only the affected_flows and solution_flows are kept in the graph"""
        for solution_object in self.solutions:
            gwalker = GraphWalker(self.graph)
            gwalker.filter_flows(solution_object)
            mask = gwalker.edge_mask
            gwalker.graph.set_edge_filter(mask)
            filtered_edges = set([(gwalker.graph.ep.id[e],gwalker.graph.ep.material[e]) for e in gwalker.graph.edges()])
            selected_flows = set(map(tuple, solution_object.affected_flows + solution_object.solution_flows))
            assert len(filtered_edges) == len(selected_flows)
            assert len(selected_flows.symmetric_difference(filtered_edges)) == 0
            # gwalker.graph.clear_filters()

    def test_graph_calculation(self):
        """Test the calculations using the graph object"""
        gwalker = GraphWalker(self.graph)
        graph2 = gwalker.calculate_solution(2.0)
        assert graph2.num_vertices() == Actor.objects.count() - ActorStock.objects.count()
        assert graph2.num_vertices() == len(self.graph.vp.id.a)
        assert graph2.num_edges() == 38
        e = next(self.graph.edges())
        assert self.graph.ep.id[e] == graph2.ep.id[e]
        assert self.graph.ep.amount[e] * 2 == graph2.ep.amount[e]

    def test_apply_solution(self):
        """Test applying the solutinos to the graph object"""
        gwsolution = GraphWalker(self.graph)
        for s in self.solutions:
            gwsolution.graph = gwsolution.calculate_solution(s.solution)

        g = gwsolution.graph
        rig = gt_util.find_vertex(g, g.vp['name'], "oil_rig_den_haag")
        assert len(rig) == 1
        refinery = gt_util.find_vertex(g, g.vp['name'], "oil_refinery_rotterdam")
        assert len(refinery) == 1
        rig_refinery = g.edge(rig[0], refinery[0], all_edges=True)
        assert len(rig_refinery) == 1
        assert g.ep.amount[rig_refinery[0]] == 120

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

'''
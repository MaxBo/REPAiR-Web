# -*- coding: utf-8 -*-

from repair.apps.asmfa.tests.flowmodeltestdata import (
    GenerateTestDataMixin,
    GenerateBigTestDataMixin)
from repair.apps.asmfa.models import Actor, Actor2Actor, ActorStock
from repair.apps.asmfa.graphs.graph import BaseGraph, GraphWalker
from django.test import TestCase
from os import path


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
        assert Actor.objects.count() == 19
        assert Actor2Actor.objects.count() == 29
        assert ActorStock.objects.count() == 2

    def test_graph_creation(self):
        """Test the Generation of the graph object"""
        assert path.isfile(self.graphbase.filename)
        assert self.graph.num_vertices() == Actor.objects.count() - ActorStock.objects.count()
        assert self.graph.num_vertices() == 17
        assert self.graph.num_vertices() == len(self.graph.vp.id.a)
        assert self.graph.num_edges() == 31
        assert self.graph.num_edges() == len(self.graph.ep.id.a)

    def test_graph_calculation(self):
        """Test the calculations using the graph object"""
        gwalker = GraphWalker(self.graph)
        graph2 = gwalker.calculate_solution(2.0)
        
        assert graph2.num_vertices() == len(self.graph.vp.id.a)
        assert graph2.num_edges() == len(self.graph.ep.id.a)
        e = self.graph.get_edges()[0]
        assert self.graph.ep.id[e] == graph2.ep.id[e]
        assert self.graph.ep.flow[e]['amount'] * 2 == graph2.ep.flow[e]['amount']
        
    def test_apply_solution(self):
        """Test applying the solutinos to the graph object"""
        gwsolution = GraphWalker(self.graph)
        for s in self.solutions:
            gwsolution.graph = gwsolution.calculate_solution(s.solution)
            
        e = self.graph.get_edges()[0]
        assert gwsolution.graph.ep.flow[e]['amount'] == 120

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

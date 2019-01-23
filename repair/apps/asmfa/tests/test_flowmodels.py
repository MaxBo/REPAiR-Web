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
        self.graphbase = BaseGraph(self.kic)
        self.graph = self.graphbase.build()
        self.gwalker = GraphWalker(self.graph)
        self.graph2 = self.gwalker.calculate_solution(2.0)

    def test_save_local(self):
        self.graph.save("/home/vagrant/REPAiR-Web/flow_modelling/cucumba_actors.gt")
        
    def test_graph_elements(self):
        """Test the Generation of the graph object"""
        # testdata
        assert Actor.objects.count() == 20
        assert Actor2Actor.objects.count() == 30
        assert ActorStock.objects.count() == 2

    def test_graph_creation(self):
        """Test the Generation of the graph object"""
        assert path.isfile(self.graphbase.filename)
        assert self.graph.num_vertices() == 19
        assert self.graph.num_vertices() == len(self.graph.vp.id.a)
        assert self.graph.num_edges() == 31
        assert self.graph.num_edges() == len(self.graph.ep.id.a)

    def test_graph_calculation(self):
        """Test the calculations using the graph object"""
        assert self.graph2.num_vertices() == 19
        assert self.graph2.num_vertices() == len(self.graph.vp.id.a)
        assert self.graph2.num_edges() == 31
        assert self.graph2.num_edges() == len(self.graph.ep.id.a)
        e = self.graph.get_edges()[0]
        assert self.graph.ep.id[e] == self.graph2.ep.id[e]
        assert self.graph.ep.flow[e]['amount'] * 2 == self.graph2.ep.flow[e]['amount']

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

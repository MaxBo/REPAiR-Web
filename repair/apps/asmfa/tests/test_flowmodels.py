# -*- coding: utf-8 -*-

from repair.apps.asmfa.tests.flowmodeltestdata import (
    GenerateTestDataMixin,
    GenerateBigTestDataMixin)
from repair.apps.asmfa.models import Actor, Actor2Actor, ActorStock
from django.test import TestCase


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

    def test_graph_elements(self):
        """Test the Generation of the graph object"""
        # testdata
        assert Actor.objects.count() == 10
        assert Actor2Actor.objects.count() == 13
        assert ActorStock.objects.count() == 2

    def test_graph_creation(self):
        """Test the Generation of the graph object"""


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

    def test_big_graph_elements(self):
        """Test the Generation of the graph object"""
        # testdata
        assert Actor.objects.count() == 1000
        assert Actor2Actor.objects.count() == 10000

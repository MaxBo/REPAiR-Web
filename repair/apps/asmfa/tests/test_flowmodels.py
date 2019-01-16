# -*- coding: utf-8 -*-

from repair.apps.asmfa.tests.flowmodeltestdata import GenerateTestDataMixin
from repair.apps.asmfa.models import Actor, Actor2Actor, ActorStock
from django.test import TestCase


class GenerateGraphTest(GenerateTestDataMixin, TestCase):
    """
    Test if the graph object is correctly generated
    """
    def test_generate_graph(self):
        """Test the Generation of the graph object"""
        # testdata
        assert Actor.objects.count() == 10
        assert Actor2Actor.objects.count() == 13
        assert ActorStock.objects.count() == 2

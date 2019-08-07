import os
from test_plus import APITestCase
from repair.apps.asmfa.graphs.graph import BaseGraph, StrategyGraph
from repair.tests.test import LoginTestCase, AdminAreaTest

from repair.apps.asmfa.factories import (ActorFactory,
                                         ActivityFactory,
                                         ActivityGroupFactory,
                                         MaterialFactory,
                                         FractionFlowFactory,
                                         AdministrativeLocationFactory
                                        )
from repair.apps.changes.factories import (StrategyFactory,
                                           SolutionInStrategyFactory,
                                           SolutionCategoryFactory,
                                           SolutionFactory,
                                           SolutionPartFactory,
                                           ImplementationQuestionFactory,
                                           ImplementationQuantityFactory,
                                           AffectedFlowFactory,
                                           ActorInSolutionPartFactory
                                        )
from repair.apps.asmfa.models import Actor, FractionFlow, StrategyFractionFlow
from repair.apps.changes.models import Solution, Strategy, ActorInSolutionPart, ImplementationQuantity, SolutionInStrategy
from repair.apps.studyarea.factories import StakeholderFactory
from repair.apps.login.factories import UserInCasestudyFactory
from django.contrib.gis.geos import Polygon, Point, GeometryCollection
from django.db.models.functions import Coalesce

class GraphTest(LoginTestCase, APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.activitygroup1 = ActivityGroupFactory(name='MyGroup',
                                                   keyflow=self.kic)
        self.activitygroup2 = ActivityGroupFactory(name='AnotherGroup',
                                                   keyflow=self.kic)
        self.activity1 = ActivityFactory(nace='NACE1',
                                         activitygroup=self.activitygroup1)
        self.activity2 = ActivityFactory(nace='NACE2',
                                         activitygroup=self.activitygroup1)
        self.activity3 = ActivityFactory(nace='NACE1',
                                         activitygroup=self.activitygroup1)
        self.activity4 = ActivityFactory(nace='NACE3',
                                         activitygroup=self.activitygroup2)

    def test_graph(self):
        self.graph = BaseGraph(self.kic, tag='test')

class StrategyGraphTest(LoginTestCase, APITestCase):
    fixtures = ['peelpioneer_data']
    
    fractionflows_count = 26
    
    #ToDo: set correct values for testing
    origin_actor_BvDid = 'SBC0011'
    new_destination_actor_BvDid = 'SBC0009'
    materialname = "Food Waste"
    fractionflows_count_for_test_actor = 2
    amount_before_shift = 5
    amount_after_shift = 4.75
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()
        
    def test_graph(self):
        self.strategy = Strategy.objects.get(pk=88)
        
        # test if peelpioneer has 26 fraction flows
        assert len(FractionFlow.objects.all()) == self.fractionflows_count        
        
        self.graph = StrategyGraph(self.strategy, tag='test')
        # delete stored graph file to test creation of data
        self.graph.remove()        
        self.graph.build()
        
        # assert graph using values
        self.assert_graph_values()
        
        # test again but now with loading the stored graph
        #self.graph.build()
        
        # assert graph using values
        #self.assert_graph_values()        
        
    def assert_graph_values(self):
        origin_actor = Actor.objects.get(BvDid=self.origin_actor_BvDid)
        new_destination_actor = Actor.objects.get(BvDid=self.new_destination_actor_BvDid)
        
        # test assertions using values above
        fractionflows = FractionFlow.objects.filter(
            origin=origin_actor).annotate(
            actual_amount=Coalesce('f_strategyfractionflow__amount', 'amount'))
        assert len(fractionflows) == self.fractionflows_count_for_test_actor
        
        # test new created flow
        ff = fractionflows.get(destination=new_destination_actor)
        assert ff.material.name == self.materialname
        assert ff.destination == new_destination_actor
        assert ff.amount == self.amount_before_shift
        assert ff.actual_amount == self.amount_after_shift

import os
from test_plus import APITestCase
from django.contrib.gis.geos import Polygon, Point, GeometryCollection
from django.db.models.functions import Coalesce
from django.contrib.gis.geos import Polygon, MultiPolygon

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
                                           FlowReferenceFactory,
                                           ImplementationQuestionFactory,
                                           ImplementationQuantityFactory,
                                           KeyflowInCasestudyFactory,
                                           PossibleImplementationAreaFactory
                                        )
from repair.apps.asmfa.models import (Actor, FractionFlow, StrategyFractionFlow,
                                      Activity, Material, KeyflowInCasestudy,
                                      CaseStudy)
from repair.apps.changes.models import (Solution, Strategy,
                                        ImplementationQuantity,
                                        SolutionInStrategy, Scheme,
                                        ImplementationArea)
from repair.apps.studyarea.factories import StakeholderFactory
from repair.apps.login.factories import UserInCasestudyFactory


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

        cls.casestudy = CaseStudy.objects.get(name='SandboxCity')
        cls.keyflow = KeyflowInCasestudy.objects.get(
            casestudy=cls.casestudy,
            keyflow__name='Food Waste')
        cls.basegraph = BaseGraph(cls.keyflow, tag='unittest')
        print('building basegraph')
        cls.basegraph.build()

    def setUp(self):
        super().setUp()
        self.solution = SolutionFactory(solution_category__keyflow=self.keyflow)
    '''
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
        new_destination_actor = Actor.objects.get(
            BvDid=self.new_destination_actor_BvDid)

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
    '''

    def test_modify(self):
        scheme = Scheme.MODIFICATION

        households = Activity.objects.get(nace='V-0000')
        collection = Activity.objects.get(nace='E-3811')
        treatment = Activity.objects.get(nace='E-3821')
        food_waste = Material.objects.get(name='Food Waste')

        possible_impl_area = PossibleImplementationAreaFactory(
            solution=self.solution,
            # should cover netherlands
            geom=MultiPolygon(
                Polygon(((3, 51), (3, 54),
                        (7.5, 54), (7.5, 51), (3, 51)))),
        )

        implementation_flow = FlowReferenceFactory(
            origin_activity=households,
            origin_area=possible_impl_area,
            destination_activity=collection,
            destination_area=possible_impl_area,
            material=food_waste
        )

        # this should double the flows
        mod_part = SolutionPartFactory(
            solution=self.solution,
            question=None,
            flow_reference=implementation_flow,
            scheme=scheme,
            is_absolute=False,
            a = 0,
            b = 2
        )

        implementation = SolutionInStrategyFactory(
            strategy__keyflow=self.keyflow,
            solution=self.solution
        )

        # set implementation area
        implementation_area = ImplementationArea.objects.get(
            implementation=implementation,
            possible_implementation_area=possible_impl_area
        )
        # same as poss. impl. area, just for testing
        implementation_area.geom = MultiPolygon(
            Polygon(((3, 51), (3, 54),
                     (7.5, 54), (7.5, 51), (3, 51))))
        implementation_area.save()

        sg = StrategyGraph(
            implementation.strategy,
            self.basegraph.tag)

        sg.build()

        original_flows = FractionFlow.objects.filter(
            origin__activity=households,
            destination__activity=collection,
            material=food_waste
        )

        changes = StrategyFractionFlow.objects.filter(
            fractionflow__in=original_flows)


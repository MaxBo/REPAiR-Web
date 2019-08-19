import os
from test_plus import APITestCase
from django.contrib.gis.geos import Polygon, Point, GeometryCollection
from django.db.models.functions import Coalesce
from django.contrib.gis.geos import Polygon, MultiPolygon
from django.db.models import Sum

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

    #fractionflows_count = 26

    ##ToDo: set correct values for testing
    #origin_actor_BvDid = 'SBC0011'
    #new_destination_actor_BvDid = 'SBC0009'
    #materialname = "Food Waste"
    #fractionflows_count_for_test_actor = 2
    #amount_before_shift = 5
    #amount_after_shift = 4.75

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

        cls.households = Activity.objects.get(nace='V-0000')
        cls.collection = Activity.objects.get(nace='E-3811')
        cls.treatment = Activity.objects.get(nace='E-3821')
        cls.food_waste = Material.objects.get(name='Food Waste')

    def setUp(self):
        super().setUp()
        self.solution = SolutionFactory(solution_category__keyflow=self.keyflow)

        self.possible_impl_area = PossibleImplementationAreaFactory(
            solution=self.solution,
            # should cover netherlands
            geom=MultiPolygon(
                Polygon(((3, 51), (3, 54),
                        (7.5, 54), (7.5, 51), (3, 51)))),
        )
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

        factor = 2

        implementation_flow = FlowReferenceFactory(
            origin_activity=self.households,
            origin_area=self.possible_impl_area,
            destination_activity=self.collection,
            destination_area=self.possible_impl_area,
            material=self.food_waste
        )

        # this should multiply the flow amounts by factor
        mod_part = SolutionPartFactory(
            solution=self.solution,
            question=None,
            flow_reference=implementation_flow,
            scheme=scheme,
            is_absolute=False,
            a = 0,
            b = factor
        )

        # create the implementation along with the strategy
        implementation = SolutionInStrategyFactory(
            strategy__keyflow=self.keyflow,
            solution=self.solution
        )

        # set implementation area
        implementation_area = ImplementationArea.objects.get(
            implementation=implementation,
            possible_implementation_area=self.possible_impl_area
        )

        # same as poss. impl. area, just for testing (you could also completely
        # skip the implementation area, possible impl. area is sufficient
        # for spatial filtering)
        implementation_area.geom = MultiPolygon(
            Polygon(((3, 51), (3, 54),
                     (7.5, 54), (7.5, 51), (3, 51))))
        implementation_area.save()

        sg = StrategyGraph(
            implementation.strategy,
            self.basegraph.tag)

        sg.build()

        # validate outcome

        status_quo_flows = FractionFlow.objects.filter(
            origin__activity=self.households,
            destination__activity=self.collection,
            material=self.food_waste,
            strategy__isnull=True, 
        )

        changes = StrategyFractionFlow.objects.filter(
            fractionflow__in=status_quo_flows)

        # the origin flows are all in the netherlands
        # and impl. area covers all of the netherlands -> all should be changed
        assert len(status_quo_flows) == len(changes), (
                f'There are {len(status_quo_flows)} status_quo_flows '
                f'and {len(changes)} changed flows. '
                f'There should be one changed flow per status quo flow')

        old_sum = status_quo_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        new_sum = changes.aggregate(
            sum_amount=Sum('amount'))['sum_amount']

        assert new_sum == old_sum * factor, (
            f'new sum: {new_sum}, old sum:{old_sum}, factor: {factor}'
        )

        # ToDo: affected flows and tests for changed new amounts

    def test_shift_destination(self):
        scheme = Scheme.SHIFTDESTINATION

        factor = 0.5

        implementation_flow = FlowReferenceFactory(
            origin_activity=self.households,
            destination_activity=self.collection,
            material=self.food_waste
        )

        # shift from collection to treatment
        shift = FlowReferenceFactory(
            destination_activity=self.treatment,
            destination_area=self.possible_impl_area,
        )

        # shift half of the amount
        shift_part = SolutionPartFactory(
            solution=self.solution,
            question=None,
            flow_reference=implementation_flow,
            flow_changes=shift,
            scheme=scheme,
            is_absolute=False,
            a = 0,
            b = factor
        )

        # create the implementation along with the strategy
        implementation = SolutionInStrategyFactory(
            strategy__keyflow=self.keyflow,
            solution=self.solution
        )

        sg = StrategyGraph(
            implementation.strategy,
            self.basegraph.tag)

        sg.build()

        status_quo_flows = FractionFlow.objects.filter(
            origin__activity=self.households,
            destination__activity=self.collection,
            material=self.food_waste,
            strategy__isnull=True
        )
        changes = StrategyFractionFlow.objects.filter(
            fractionflow__in=status_quo_flows)

        new_flows = FractionFlow.objects.filter(
            origin__activity=self.households,
            destination__activity=self.treatment,
            material=self.food_waste,
            strategy=implementation.strategy
        )

        assert len(status_quo_flows) ==  len(new_flows)

        # original flows should have been reduced
        old_sum = status_quo_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        new_sum = changes.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        assert new_sum == old_sum * factor

        # ToDo: additional asserts, affected flows

    def test_new_flows(self):
        scheme = Scheme.NEW

        new_flow = FlowReferenceFactory(
            origin_activity=self.collection,
            destination_activity=self.treatment,
            material=self.food_waste
        )

        amount = 1000

        new_part = SolutionPartFactory(
            solution=self.solution,
            question=None,
            flow_changes=new_flow,
            scheme=scheme,
            is_absolute=True,
            a = 0,
            b = amount
        )

        # create the implementation along with the strategy
        implementation = SolutionInStrategyFactory(
            strategy__keyflow=self.keyflow,
            solution=self.solution
        )

        sg = StrategyGraph(
            implementation.strategy,
            self.basegraph.tag)

        sg.build()
        
        changes = StrategyFractionFlow.objects.all()
        
        assert not changes, (
            f'there should be no changes, '
            f'but there are {len(changes)} changed flows')

        new_flows = FractionFlow.objects.filter(
            origin__activity=self.collection,
            destination__activity=self.treatment,
            material=self.food_waste,
            strategy=implementation.strategy
        )
        
        
        new_sum = new_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        assert new_sum == amount, (
            f'new_flow should have the amount of {amount} of the strategy, '
            f'but has an amount of {new_sum} '
            f"and values of {new_flows.values_list('amount')}"
        )

        # ToDo: asserts, affected flows

    def test_append(self):
        scheme = Scheme.APPEND

        factor = 0.5

        implementation_flow = FlowReferenceFactory(
            origin_activity=self.households,
            destination_activity=self.collection,
            material=self.food_waste
        )

        # shift from collection to treatment
        appendix = FlowReferenceFactory(
            destination_activity=self.treatment,
            destination_area=self.possible_impl_area,
        )

        # shift half of the amount
        shift_part = SolutionPartFactory(
            solution=self.solution,
            question=None,
            flow_reference=implementation_flow,
            flow_changes=appendix,
            scheme=scheme,
            is_absolute=False,
            a = 0,
            b = factor
        )

        # create the implementation along with the strategy
        implementation = SolutionInStrategyFactory(
            strategy__keyflow=self.keyflow,
            solution=self.solution
        )

        sg = StrategyGraph(
            implementation.strategy,
            self.basegraph.tag)

        sg.build()

        status_quo_flows = FractionFlow.objects.filter(
            origin__activity=self.households,
            destination__activity=self.collection,
            material=self.food_waste,
            strategy__isnull=True
        )

        changed_flows = StrategyFractionFlow.objects.filter(
            fractionflow__in=status_quo_flows)

        new_flows = FractionFlow.objects.filter(
            origin__activity=self.households,
            destination__activity=self.treatment,
            material=self.food_waste,
            strategy=implementation.strategy
        )

        # there are some that are changed instead of newly created
        # (because there already are some existing)
        assert len(status_quo_flows) == len(new_flows) + len(changed_flows)

        # ToDo: additional asserts (test origins/destinations), affected flows

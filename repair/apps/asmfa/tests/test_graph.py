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
                                      CaseStudy, Process)
from repair.apps.changes.models import (Solution, Strategy,
                                        ImplementationQuantity,
                                        SolutionInStrategy, Scheme,
                                        ImplementationArea)
from repair.apps.studyarea.factories import StakeholderFactory
from repair.apps.login.factories import UserInCasestudyFactory

from repair.apps.changes.tests.test_graphwalker import MultiplyTestDataMixin


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
        cls.orange_product = Material.objects.get(name='Essential Orange oils')

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

        flow_changes = FlowReferenceFactory(
            material=self.orange_product,
            waste=0
        )

        # this should multiply the flow amounts by factor
        mod_part = SolutionPartFactory(
            solution=self.solution,
            question=None,
            flow_reference=implementation_flow,
            flow_changes=flow_changes,
            scheme=scheme,
            is_absolute=False,
            a = 0,
            b = factor
        )

        AffectedFlowFactory(
            origin_activity=self.collection,
            destination_activity=self.treatment,
            solution_part=mod_part,
            material=self.food_waste
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

        impl_flows = FractionFlow.objects.filter(
            origin__activity=self.households,
            destination__activity=self.collection,
            material=self.food_waste,
            strategy__isnull=True,
        )

        affected_flows = FractionFlow.objects.filter(
            origin__activity=self.collection,
            destination__activity=self.treatment,
            material=self.food_waste,
            strategy__isnull=True,
        )

        impl_changes = StrategyFractionFlow.objects.filter(
            fractionflow__in=impl_flows,
            strategy=implementation.strategy)

        aff_changes = StrategyFractionFlow.objects.filter(
            fractionflow__in=affected_flows,
            strategy=implementation.strategy)

        materials = impl_changes.values_list('material', flat=True).distinct()
        waste = impl_changes.values_list('waste', flat=True).distinct()
        assert (len(materials) == 1 and
                materials[0] == self.orange_product.id), (
                    "The material was supposed to change but didn't "
                    "change in database")
        assert (len(waste) == 1 and
                waste[0] == False), (
                    "The flows were supposed to change from from product to "
                    "waste but didn't change in database")

        # the origin flows are all in the netherlands
        # and impl. area covers all of the netherlands -> all should be changed
        assert len(impl_flows) == len(impl_changes), (
                f'There are {len(impl_flows)} implementation flows '
                f'and {len(impl_changes)} changes to those. '
                f'There should be one changed flow per implementation flow')

        impl_old_sum = impl_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        impl_new_sum = impl_changes.aggregate(
            sum_amount=Sum('amount'))['sum_amount']

        assert impl_new_sum == impl_old_sum * factor, (
            f'new sum: {impl_new_sum}, old sum:{impl_old_sum}, factor: {factor}'
        )

        assert len(affected_flows) == len(aff_changes), (
                f'There are {len(affected_flows)} affected flows '
                f'and {len(aff_changes)} changes to those. '
                f'There should be one changed flow per affected flow')

        aff_old_sum = affected_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        aff_new_sum = aff_changes.aggregate(
            sum_amount=Sum('amount'))['sum_amount']

        assert aff_new_sum == (impl_new_sum - impl_old_sum) + aff_old_sum


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
            material=self.orange_product,
            waste=0
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
            fractionflow__in=status_quo_flows,
            strategy=implementation.strategy)

        new_flows = FractionFlow.objects.filter(
            origin__activity=self.households,
            destination__activity=self.treatment,
            material=self.orange_product,
            strategy=implementation.strategy
        )

        assert len(status_quo_flows) == len(new_flows)

        materials = new_flows.values_list('material', flat=True).distinct()
        waste = new_flows.values_list('waste', flat=True).distinct()
        assert (len(materials) == 1 and
                materials[0] == self.orange_product.id), (
                    "The material was supposed to change but didn't "
                    "change in database")
        assert (len(waste) == 1 and
                waste[0] == False), (
                    "The flows were supposed to change from from product to "
                    "waste but didn't change in database")

        # original flows should have been reduced
        old_sum = status_quo_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        new_sum = changes.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        new_flow_sum = new_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']

        msg = f'new_sum: {new_sum} should be factor: {factor} * old_sum: {old_sum}'
        self.assertAlmostEqual(new_sum, old_sum*factor, msg=msg)
        msg = f'new_flow_sum: {new_flow_sum} should be the difference of old_sum: {old_sum} - new_sum: {new_sum}'
        self.assertAlmostEqual(new_flow_sum, old_sum - new_sum, msg=msg)

        # ToDo: additional asserts, affected flows

    def test_shift_origin(self):
        scheme = Scheme.SHIFTORIGIN

        factor = 0.5

        implementation_flow = FlowReferenceFactory(
            origin_activity=self.households,
            destination_activity=self.treatment,
            material=self.food_waste
        )

        # shift from households to collection
        shift = FlowReferenceFactory(
            origin_activity=self.collection,
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
            destination__activity=self.treatment,
            material=self.food_waste,
            strategy__isnull=True
        )
        changes = StrategyFractionFlow.objects.filter(
            fractionflow__in=status_quo_flows)

        new_flows = FractionFlow.objects.filter(
            origin__activity=self.collection,
            destination__activity=self.treatment,
            material=self.food_waste,
            strategy=implementation.strategy
        )

        assert len(status_quo_flows) == len(new_flows)

        # original flows should have been reduced
        old_sum = status_quo_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        new_sum = changes.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        new_flow_sum = new_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']

        assert new_sum == old_sum * factor
        assert new_flow_sum == old_sum - new_sum

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

    def test_prepend(self):
        scheme = Scheme.PREPEND

        factor = 0.5

        implementation_flow = FlowReferenceFactory(
            origin_activity=self.collection,
            destination_activity=self.treatment,
            material=self.food_waste
        )

        # shift from collection to treatment
        prefix = FlowReferenceFactory(
            origin_activity=self.households,
            origin_area=self.possible_impl_area,
            material=self.orange_product,
            waste=0
        )

        # shift half of the amount
        shift_part = SolutionPartFactory(
            solution=self.solution,
            question=None,
            flow_reference=implementation_flow,
            flow_changes=prefix,
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
            origin__activity=self.collection,
            destination__activity=self.treatment,
            material=self.food_waste,
            strategy__isnull=True
        )

        new_flows = FractionFlow.objects.filter(
            origin__activity=self.households,
            destination__activity=self.collection,
            material=self.orange_product,
            strategy=implementation.strategy
        )

        sq_sum = status_quo_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        prep_sum = new_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']

        assert len(status_quo_flows) == len(new_flows)
        assert prep_sum == sq_sum * factor

        materials = new_flows.values_list('material', flat=True).distinct()
        waste = new_flows.values_list('waste', flat=True).distinct()
        assert (len(materials) == 1 and
                materials[0] == self.orange_product.id), (
                    "The material was supposed to change but didn't "
                    "change in database")
        assert (len(waste) == 1 and
                waste[0] == False), (
                    "The flows were supposed to change from from product to "
                    "waste but didn't change in database")

        # ToDo: additional asserts (test origins/destinations), affected flows

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
            origin__activity=self.collection,
            destination__activity=self.treatment,
            material=self.food_waste,
            strategy=implementation.strategy
        )

        sq_sum = status_quo_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        app_sum = new_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']

        assert len(status_quo_flows) == len(new_flows)
        assert app_sum == sq_sum * factor

        # ToDo: additional asserts (test origins/destinations), affected flows


class PeelPioneerTest(LoginTestCase, APITestCase):
    fixtures = ['peelpioneer_data']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.casestudy = CaseStudy.objects.get(name='SandboxCity')
        cls.keyflow = KeyflowInCasestudy.objects.get(
            casestudy=cls.casestudy,
            keyflow__name='Food Waste')
        cls.basegraph = BaseGraph(cls.keyflow, tag='unittest')
        cls.basegraph.build()

        cls.restaurants = Activity.objects.get(nace='I-5610')
        cls.retail = Activity.objects.get(nace='G-4711')
        cls.treatment = Activity.objects.get(nace='E-3821')
        cls.processing = Activity.objects.get(nace='C-1030')
        cls.pharma_manufacture = Activity.objects.get(nace='C-2110')
        cls.textile_manufacture = Activity.objects.get(nace='C-1399')

        cls.food_waste = Material.objects.get(name='Food Waste')
        cls.organic_waste = Material.objects.get(name='Organic Waste')
        cls.orange_peel = Material.objects.get(name='Orange Peel')
        cls.essential_oils = Material.objects.get(name='Essential Orange oils')
        cls.fiber = Material.objects.get(name='Orange fibers')

        cls.incineration = Process.objects.get(name='Incineration')

    def setUp(self):
        super().setUp()
        self.solution = SolutionFactory(solution_category__keyflow=self.keyflow)

    def test_solution(self):

        # create the implementation along with the strategy
        implementation = SolutionInStrategyFactory(
            strategy__keyflow=self.keyflow,
            solution=self.solution
        )

        question = ImplementationQuestionFactory(
            question='How much orange peel waste will be used?',
            min_value=0,
            max_value=1,
            is_absolute=False,
            solution=self.solution
        )

        answer = ImplementationQuantityFactory(
            question=question,
            value=1,
            implementation=implementation
        )

        priority = 0

        ### shift food waste from treatment to processing ###
        ### -> new orange peel flows ###

        restaurants_to_treat = FlowReferenceFactory(
            origin_activity=self.restaurants,
            destination_activity=self.treatment,
            material=self.food_waste,
            process=self.incineration
        )

        retail_to_treat = FlowReferenceFactory(
            origin_activity=self.retail,
            destination_activity=self.treatment,
            material=self.food_waste,
            process=self.incineration
        )

        # ToDo: change process?
        shift_to_processing = FlowReferenceFactory(
            destination_activity=self.processing,
            material=self.orange_peel
        )

        # part to shift flows from restaurants
        SolutionPartFactory(
            solution=self.solution,
            question=question,
            flow_reference=restaurants_to_treat,
            flow_changes=shift_to_processing,
            scheme=Scheme.SHIFTDESTINATION,
            a=0.05,
            b=0,
            priority=priority
        )
        priority += 1

        # part to shift flows from retail
        SolutionPartFactory(
            solution=self.solution,
            question=question,
            flow_reference=retail_to_treat,
            flow_changes=shift_to_processing,
            scheme=Scheme.SHIFTDESTINATION,
            a=0.05,
            b=0,
            priority=priority
        )
        priority += 1

        ### prepend flows to the orange peel flows ###

        # Warning: if there would already be orange peel coming from restaurants
        # or retail to processing it takes 50% of all of those
        # (not only the new ones)

        rest_to_proc = FlowReferenceFactory(
            origin_activity=self.restaurants,
            destination_activity=self.processing,
            material=self.orange_peel
        )

        retail_to_proc = FlowReferenceFactory(
            origin_activity=self.retail,
            destination_activity=self.processing,
            material=self.orange_peel
        )

        append_treatment = FlowReferenceFactory(
            destination_activity=self.treatment,
            material=self.organic_waste
        )

        # part to prepend to restaurant-processing flows going to treatment
        SolutionPartFactory(
            solution=self.solution,
            flow_reference=rest_to_proc,
            flow_changes=append_treatment,
            scheme=Scheme.APPEND,
            b=0.5,
            priority=priority
        )
        priority += 1

        # part to prepend flows to retail-processing flows going to treatment
        SolutionPartFactory(
            solution=self.solution,
            flow_reference=retail_to_proc,
            flow_changes=append_treatment,
            scheme=Scheme.APPEND,
            b=0.5,
            priority=priority
        )
        priority += 1

        append_textile = FlowReferenceFactory(
            destination_activity=self.textile_manufacture,
            material=self.fiber,
            waste=0
        )

        # part to prepend to restaurant-processing flows going to textile manu.
        SolutionPartFactory(
            solution=self.solution,
            flow_reference=rest_to_proc,
            flow_changes=append_textile,
            scheme=Scheme.APPEND,
            b=0.03,
            priority=priority
        )
        priority += 1

        # part to prepend to retail-processing flows going to textile manu.
        SolutionPartFactory(
            solution=self.solution,
            flow_reference=retail_to_proc,
            flow_changes=append_textile,
            scheme=Scheme.APPEND,
            b=0.03,
            priority=priority
        )
        priority += 1

        append_pharma = FlowReferenceFactory(
            destination_activity=self.pharma_manufacture,
            material=self.essential_oils,
            waste=0
        )

        # part to prepend to restaurant-processing flows going to pharma
        SolutionPartFactory(
            solution=self.solution,
            flow_reference=rest_to_proc,
            flow_changes=append_pharma,
            scheme=Scheme.APPEND,
            b=0.01,
            priority=priority
        )
        priority += 1

        # part to prepend to retail-processing flows going to pharma
        SolutionPartFactory(
            solution=self.solution,
            flow_reference=retail_to_proc,
            flow_changes=append_pharma,
            scheme=Scheme.APPEND,
            b=0.01,
            priority=priority
        )
        priority += 1

        sg = StrategyGraph(
            implementation.strategy,
            self.basegraph.tag)

        sg.build()

        sq_flows = FractionFlow.objects.filter(
            origin__activity__nace='G-4711',
            destination__activity__nace='E-3821'
        )
        # was filtered by process
        strat_flows = StrategyFractionFlow.objects.filter(
            strategy=implementation.strategy,
            fractionflow__in=sq_flows)

        for strat_flow in strat_flows:
            sq_flow = strat_flow.fractionflow.amount

        sq_flows = FractionFlow.objects.filter(
            origin__activity__nace='I-5610',
            destination__activity__nace='E-3821'
        )
        strat_flows = StrategyFractionFlow.objects.filter(
            strategy=implementation.strategy,
            fractionflow__in=sq_flows)


class StrategyGraphPerformanceTest(MultiplyTestDataMixin,
                                   StrategyGraphTest):
    """The same tests but with bigger data"""

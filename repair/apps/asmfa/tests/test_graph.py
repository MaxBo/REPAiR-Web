import os
from test_plus import APITestCase
from django.contrib.gis.geos import Polygon, Point, GeometryCollection
from django.db.models.functions import Coalesce
from django.contrib.gis.geos import Polygon, MultiPolygon
from django.db.models import Sum
from django.test import TestCase

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
from repair.apps.asmfa.tests import flowmodeltestdata


class GraphWalkerTest(TestCase):

    def test_data_creation(self):
        b2b = flowmodeltestdata.bread_to_beer_graph()
        assert b2b.num_vertices() == 6
        assert b2b.num_edges() == 6
        plastic = flowmodeltestdata.plastic_package_graph()
        assert plastic.num_vertices() == 12
        assert plastic.num_edges() == 15

    def test_plot(self):
        b2b = flowmodeltestdata.bread_to_beer_graph()
        flowmodeltestdata.plot_amounts(b2b, 'breadtobeer_amounts.png')
        flowmodeltestdata.plot_materials(b2b, 'breadtobeer_materials.png')
        plastic = flowmodeltestdata.plastic_package_graph()
        flowmodeltestdata.plot_amounts(plastic, 'plastic_amounts.png')
        flowmodeltestdata.plot_materials(plastic, 'plastic_materials.png')


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
                Polygon(((2, 50), (2, 55),
                         (9, 55), (9, 50), (2, 50)))),
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
        implementation_area.geom = self.possible_impl_area.geom
        #MultiPolygon(
            #Polygon(((2.5, 50.5), (2.5, 54.5),
                     #(8, 54.5), (8, 50.5), (2.5, 50.5))))
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

        self.assertAlmostEqual(impl_new_sum, impl_old_sum * factor,
            msg=(f'new sum: {impl_new_sum}, '
                 f'old sum:{impl_old_sum}, factor: {factor}')
        )

        # ToDo: those tests only work for the fixed test-set, not work
        # for the randomly extendet dataset, because not all affected flows are
        # actually affected (not connected to impl. flows)
        # what can we test here

        #assert len(affected_flows) == len(aff_changes), (
                #f'There are {len(affected_flows)} affected flows '
                #f'and {len(aff_changes)} changes to those. '
                #f'There should be one changed flow per affected flow')

        aff_old_sum = affected_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        aff_new_sum = aff_changes.aggregate(
            sum_amount=Sum('amount'))['sum_amount']

        #self.assertAlmostEqual(aff_new_sum,
                               #(impl_new_sum - impl_old_sum) + aff_old_sum)


    def test_shift_destination(self):
        scheme = Scheme.SHIFTDESTINATION

        factor = 0.2

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

        msg = f'new sum is {new_sum}, expected: {old_sum-old_sum*factor}'
        self.assertAlmostEqual(new_sum, old_sum-old_sum*factor, msg=msg)
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

        self.assertAlmostEqual(new_sum, old_sum - old_sum * factor)
        self.assertAlmostEqual(new_flow_sum, old_sum - new_sum)

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
        msg = (f'new_flow should have the amount of {amount} of the strategy, '
               f'but has an amount of {new_sum} '
               f"and values of {new_flows.values_list('amount', flat=True)}")
        self.assertAlmostEqual(new_sum, amount, msg=msg)

        # ToDo: asserts, affected flows

    def test_prepend(self):
        scheme = Scheme.PREPEND

        factor = 0.3

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
        self.assertAlmostEqual(
            prep_sum, sq_sum * factor,
            msg=f'new flows sum up to {prep_sum}, expected: {sq_sum * factor}')

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

        factor = 0.8

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
        self.assertAlmostEqual(app_sum, sq_sum * factor)

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
        cls.retail_food = Activity.objects.get(nace='G-4711')
        cls.treatment = Activity.objects.get(nace='E-3821')
        cls.processing = Activity.objects.get(nace='C-1030')
        cls.pharma_manufacture = Activity.objects.get(nace='C-2110')
        cls.textile_manufacture = Activity.objects.get(nace='C-1399')
        cls.retail_cosmetics = Activity.objects.get(nace='G-4775')
        cls.petroleum_manufacture = Activity.objects.get(nace='C-1920')

        cls.food_waste = Material.objects.get(name='Food Waste')
        cls.organic_waste = Material.objects.get(name='Organic Waste')
        cls.orange_peel = Material.objects.get(name='Orange Peel')
        cls.essential_oils = Material.objects.get(name='Essential Orange oils')
        cls.fiber = Material.objects.get(name='Orange fibers')
        cls.biofuel = Material.objects.get(name='Biofuel')

        cls.incineration = Process.objects.get(name='Incineration')

    def setUp(self):
        super().setUp()
        self.solution = SolutionFactory(solution_category__keyflow=self.keyflow)

        # create the implementation along with the strategy
        self.implementation = SolutionInStrategyFactory(
            strategy__keyflow=self.keyflow,
            solution=self.solution
        )

    def test_solution(self):

        original_flow_count = FractionFlow.objects.count()
        original_strat_flow_count = StrategyFractionFlow.objects.count()

        new_flow_count = 0
        new_strat_flow_count = 0

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
            implementation=self.implementation
        )

        priority = 0

        ### shift food waste from treatment to processing ###
        ### -> new orange peel flows ###

        restaurants_to_treat = FlowReferenceFactory(
            origin_activity=self.restaurants,
            destination_activity=self.treatment,
            material=self.food_waste
        )

        retail_to_treat = FlowReferenceFactory(
            origin_activity=self.retail_food,
            destination_activity=self.treatment,
            material=self.food_waste
        )

        # ToDo: change process?
        shift_to_processing = FlowReferenceFactory(
            destination_activity=self.processing,
            material=self.orange_peel
        )

        # part to shift flows from restaurants
        part = SolutionPartFactory(
            name='shift flows from restaurants',
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

        AffectedFlowFactory(
            origin_activity=self.treatment,
            destination_activity=self.petroleum_manufacture,
            solution_part=part,
            material=self.biofuel
        )

        # part to shift flows from retail
        part = SolutionPartFactory(
            name='shift flows from retail',
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

        AffectedFlowFactory(
            origin_activity=self.treatment,
            destination_activity=self.petroleum_manufacture,
            solution_part=part,
            material=self.biofuel
        )

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
            origin_activity=self.retail_food,
            destination_activity=self.processing,
            material=self.orange_peel
        )

        append_treatment = FlowReferenceFactory(
            destination_activity=self.treatment,
            material=self.organic_waste,
            waste=1
        )

        # part to append to restaurant-processing flows going to treatment
        part = SolutionPartFactory(
            name='append to restaurant->processing -> treatment',
            solution=self.solution,
            flow_reference=rest_to_proc,
            flow_changes=append_treatment,
            scheme=Scheme.APPEND,
            b=0.5,
            priority=priority
        )
        priority += 1

        AffectedFlowFactory(
            origin_activity=self.treatment,
            destination_activity=self.petroleum_manufacture,
            solution_part=part,
            material=self.biofuel
        )

        # part to append flows to retail-processing flows going to treatment
        part = SolutionPartFactory(
            name='append to retail->processing -> treatment',
            solution=self.solution,
            flow_reference=retail_to_proc,
            flow_changes=append_treatment,
            scheme=Scheme.APPEND,
            b=0.5,
            priority=priority
        )
        priority += 1

        AffectedFlowFactory(
            origin_activity=self.treatment,
            destination_activity=self.petroleum_manufacture,
            solution_part=part,
            material=self.biofuel
        )

        append_textile = FlowReferenceFactory(
            destination_activity=self.textile_manufacture,
            material=self.fiber,
            waste=0
        )

        # part to append to restaurant-processing flows going to textile manu.
        SolutionPartFactory(
            name='append to restaurant->processing -> textile',
            solution=self.solution,
            flow_reference=rest_to_proc,
            flow_changes=append_textile,
            scheme=Scheme.APPEND,
            b=0.03,
            priority=priority
        )
        priority += 1

        # part to append to retail-processing flows going to textile manu.
        SolutionPartFactory(
            name='append to retail->processing -> textile',
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

        # part to append to restaurant-processing flows going to pharma
        part = SolutionPartFactory(
            name='append to restaurant->processing -> pharma',
            solution=self.solution,
            flow_reference=rest_to_proc,
            flow_changes=append_pharma,
            scheme=Scheme.APPEND,
            b=0.01,
            priority=priority
        )
        priority += 1

        AffectedFlowFactory(
            origin_activity=self.pharma_manufacture,
            destination_activity=self.retail_cosmetics,
            solution_part=part,
            material=self.essential_oils
        )

        # part to append to retail-processing flows going to pharma
        part = SolutionPartFactory(
            name='append to retail->processing -> pharma',
            solution=self.solution,
            flow_reference=retail_to_proc,
            flow_changes=append_pharma,
            scheme=Scheme.APPEND,
            b=0.01,
            priority=priority
        )
        priority += 1

        AffectedFlowFactory(
            origin_activity=self.pharma_manufacture,
            destination_activity=self.retail_cosmetics,
            solution_part=part,
            material=self.essential_oils
        )

        # build graph and calculate strategy

        sg = StrategyGraph(
            self.implementation.strategy,
            self.basegraph.tag)

        sg.build()

        ### check shift from restaurants to processing ###

        sq_rest_to_treat = FractionFlow.objects.filter(
            origin__activity=self.restaurants,
            destination__activity=self.treatment,
            strategy__isnull=True
        )
        strat_flows = StrategyFractionFlow.objects.filter(
            strategy=self.implementation.strategy,
            fractionflow__in=sq_rest_to_treat
        )
        new_strat_flow_count += strat_flows.count()
        new_rest_to_proc = FractionFlow.objects.filter(
            strategy=self.implementation.strategy,
            origin__activity=self.restaurants,
            destination__activity=self.processing
        )
        new_flow_count += new_rest_to_proc.count()

        sq_rest_to_treat_sum = sq_rest_to_treat.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        strat_sum = strat_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        new_rest_to_proc_sum = new_rest_to_proc.aggregate(
            sum_amount=Sum('amount'))['sum_amount']

        self.assertAlmostEqual(strat_sum, sq_rest_to_treat_sum * 0.95)
        self.assertAlmostEqual(new_rest_to_proc_sum,
                               sq_rest_to_treat_sum * 0.05)

        for strat_flow in strat_flows:
            sq_amount = strat_flow.fractionflow.amount
            origin = strat_flow.fractionflow.origin
            process = strat_flow.fractionflow.process
            new_flow = new_rest_to_proc.get(origin=origin, process=process)
            self.assertAlmostEqual(strat_flow.amount,
                                   sq_amount - sq_amount * 0.05)
            self.assertAlmostEqual(new_flow.amount, sq_amount * 0.05)
            assert new_flow.material == self.orange_peel
            assert new_flow.waste == True

        ### check shift from retail to processing ###

        sq_retail_to_treat = FractionFlow.objects.filter(
            origin__activity=self.retail_food,
            destination__activity=self.treatment,
            strategy__isnull=True
        )
        strat_flows = StrategyFractionFlow.objects.filter(
            strategy=self.implementation.strategy,
            fractionflow__in=sq_retail_to_treat
        )
        new_strat_flow_count += strat_flows.count()
        new_retail_to_proc = FractionFlow.objects.filter(
            strategy=self.implementation.strategy,
            origin__activity=self.retail_food,
            destination__activity=self.processing
        )
        new_flow_count += new_retail_to_proc.count()

        sq_retail_to_treat_sum = sq_retail_to_treat.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        strat_sum = strat_flows.aggregate(
            sum_amount=Sum('amount'))['sum_amount']
        new_retail_to_proc_sum = new_retail_to_proc.aggregate(
            sum_amount=Sum('amount'))['sum_amount']

        self.assertAlmostEqual(strat_sum, sq_retail_to_treat_sum * 0.95)
        self.assertAlmostEqual(new_retail_to_proc_sum,
                               sq_retail_to_treat_sum * 0.05)

        for strat_flow in strat_flows:
            sq_amount = strat_flow.fractionflow.amount
            origin = strat_flow.fractionflow.origin
            process = strat_flow.fractionflow.process
            new_flow = new_retail_to_proc.get(origin=origin, process=process)
            self.assertAlmostEqual(strat_flow.amount,
                                   sq_amount - sq_amount * 0.05)
            self.assertAlmostEqual(new_flow.amount, sq_amount * 0.05)
            assert new_flow.material == self.orange_peel
            assert new_flow.waste == True

        ### check processing to treatment ###

        new_proc_to_treat = FractionFlow.objects.filter(
            strategy=self.implementation.strategy,
            origin__activity=self.processing,
            destination__activity=self.treatment
        )
        new_flow_count += new_proc_to_treat.count()

        new_proc_to_treat_sum = new_proc_to_treat.aggregate(
            sum_amount=Sum('amount'))['sum_amount']

        self.assertAlmostEqual(
            new_proc_to_treat_sum,
            (new_rest_to_proc_sum + new_retail_to_proc_sum) * 0.5)

        materials = new_proc_to_treat.values_list(
            'material', flat=True).distinct()
        waste = new_proc_to_treat.values_list(
            'waste', flat=True).distinct()
        assert (len(materials) == 1 and materials[0] == self.organic_waste.id)
        assert (len(waste) == 1 and waste[0] == True)

        ### check processing to textile manufacture ###

        new_proc_to_textile = FractionFlow.objects.filter(
            strategy=self.implementation.strategy,
            origin__activity=self.processing,
            destination__activity=self.textile_manufacture
        )
        new_flow_count += new_proc_to_textile.count()

        new_proc_to_textile_sum = new_proc_to_textile.aggregate(
            sum_amount=Sum('amount'))['sum_amount']

        self.assertAlmostEqual(
            new_proc_to_textile_sum,
            (new_rest_to_proc_sum + new_retail_to_proc_sum) * 0.03)

        materials = new_proc_to_textile.values_list(
            'material', flat=True).distinct()
        waste = new_proc_to_textile.values_list(
            'waste', flat=True).distinct()
        assert (len(materials) == 1 and materials[0] == self.fiber.id)
        assert (len(waste) == 1 and waste[0] == False)

        ### check processing to pharma manufacture ###

        new_proc_to_pharma = FractionFlow.objects.filter(
            strategy=self.implementation.strategy,
            origin__activity=self.processing,
            destination__activity=self.pharma_manufacture
        )
        new_flow_count += new_proc_to_pharma.count()

        new_proc_to_pharma_sum = new_proc_to_pharma.aggregate(
            sum_amount=Sum('amount'))['sum_amount']

        self.assertAlmostEqual(
            new_proc_to_pharma_sum,
            (new_rest_to_proc_sum + new_retail_to_proc_sum) * 0.01)

        materials = new_proc_to_pharma.values_list(
            'material', flat=True).distinct()
        waste = new_proc_to_pharma.values_list(
            'waste', flat=True).distinct()
        assert (len(materials) == 1 and materials[0] == self.essential_oils.id)
        assert (len(waste) == 1 and waste[0] == False)

        ### check affected flows ###

        sq_petroleum_flows = FractionFlow.objects.filter(
            origin__activity=self.treatment,
            destination__activity=self.petroleum_manufacture,
            material=self.biofuel,
            strategy__isnull=True
        )
        affected_petroleum = StrategyFractionFlow.objects.filter(
            fractionflow__in=sq_petroleum_flows)

        biodigester = Actor.objects.get(BvDid='SBC0010')
        sq_in_digester = FractionFlow.objects.filter(
            destination=biodigester,
            strategy__isnull=True)
        sq_out_digester = FractionFlow.objects.filter(
            origin=biodigester,
            strategy__isnull=True)
        strat_in_digester = FractionFlow.objects.filter(
            destination=biodigester,
            ).annotate(
                s_amount=Coalesce('f_strategyfractionflow__amount', 'amount')
            )
        strat_out_digester = FractionFlow.objects.filter(
            origin=biodigester,
            ).annotate(
                s_amount=Coalesce('f_strategyfractionflow__amount', 'amount')
            )
        sq_in_digester_sum = sq_in_digester.aggregate(
            amount=Sum('amount'))['amount']
        sq_out_digester_sum = sq_out_digester.aggregate(
            amount=Sum('amount'))['amount']
        strat_in_digester_sum = strat_in_digester.aggregate(
            amount=Sum('s_amount'))['amount']
        strat_out_digester_sum = strat_out_digester.aggregate(
            amount=Sum('s_amount'))['amount']
        assert sq_in_digester_sum > strat_in_digester_sum, (
            'the input to treatment should be reduced in strategy')

        sq_digest_factor = sq_out_digester_sum / sq_in_digester_sum
        strat_digest_factor = strat_out_digester_sum / strat_in_digester_sum

        self.assertAlmostEqual(sq_digest_factor, strat_digest_factor,
                               msg=f'the factor at actor {biodigester} in '
                               'strategy has to the stay same as in status quo')

        ## all are affected (and not more than one per flow created)
        #assert len(sq_petroleum_flows) == len(affected_petroleum)
        #sq_petroleum_sum = sq_petroleum_flows.aggregate(
            #amount=Sum('amount'))['amount']
        #aff_petroleum_sum = affected_petroleum.aggregate(
            #amount=Sum('amount'))['amount']
        #assert sq_petroleum_sum > aff_petroleum_sum, (
            #'the affected flows to petroleum manufacture should be reduced '
            #'in strategy')

        sq_cosmetic_flows = FractionFlow.objects.filter(
            origin__activity=self.pharma_manufacture,
            destination__activity=self.retail_cosmetics)
        affected_cosmetics = StrategyFractionFlow.objects.filter(
            fractionflow__in=sq_cosmetic_flows)

        # ToDo: what do we expect here?
        assert len(affected_cosmetics) == 0

        ### check that there are no other flows affected ###

        assert FractionFlow.objects.count() == (
                new_flow_count + original_flow_count)
        assert StrategyFractionFlow.objects.count() == (
                sq_rest_to_treat.count() + sq_retail_to_treat.count() +
                sq_petroleum_flows.count() + sq_cosmetic_flows.count())
        assert StrategyFractionFlow.objects.count() == (
            new_strat_flow_count + affected_petroleum.count())


class StrategyGraphPerformanceTest(MultiplyTestDataMixin,
                                   StrategyGraphTest):
    """The same tests but with bigger data"""

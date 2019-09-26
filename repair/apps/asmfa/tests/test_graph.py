import os
from test_plus import APITestCase
from django.contrib.gis.geos import Polygon, Point, GeometryCollection
from django.db.models.functions import Coalesce
from django.db.models import Case, When, Value, F
from django.contrib.gis.geos import Polygon, MultiPolygon
from django.db.models import Sum
from django.test import TestCase

from repair.apps.asmfa.graphs.graph import BaseGraph, StrategyGraph
from repair.apps.asmfa.graphs.graphwalker import GraphWalker
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

    def test_plastic_packaging(self):
        """Reduce plastic between Packaging->Consumption

        Results (change in tons):
            Packaging --> Consumption -0.6017
            Oil rig --> Oil refinery -0.6017
            Oil refinery --> Production -0.48136
            Production --> Packaging -0.6017
            Consumption --> Burn -0.36102
            Consumption --> Recycling -0.24068
            Recycling --> Production -0.12034
        """
        plastic = flowmodeltestdata.plastic_package_graph()
        gw = GraphWalker(plastic)
        change = gw.graph.new_edge_property('float')
        gw.graph.edge_properties['change'] = change
        changed = gw.graph.new_edge_property('bool',
                                             vals=[False for e in range(gw.graph.num_edges())])
        gw.graph.edge_properties['changed'] = changed
        include = gw.graph.new_edge_property('bool')
        gw.graph.edge_properties['include'] = include
        bf = gw.graph.new_vertex_property('float',
                                          vals=[1.0 for v in range(gw.graph.num_vertices())])
        gw.graph.vertex_properties['downstream_balance_factor'] = bf
        pe = gw.graph.edge(gw.graph.vertex(1), gw.graph.vertex(6),
                           all_edges=True)  # the 3 edges between Packaging and Cosumption
        implementation_edges = [e for e in pe
                                if gw.graph.ep.material[e] == 'plastic']
        # reduce the Plastic by 0.3 tons on the implementation_edge
        deltas = [-0.6017]
        # select affected flows
        for i, e in enumerate(gw.graph.edges()):
            # flows of 'plastic' or 'crude oil' are affected by the solution
            if gw.graph.ep.material[e] in ['plastic', 'crude oil']:
                gw.graph.ep.include[e] = True
            else:
                gw.graph.ep.include[e] = False
        result = gw.calculate(implementation_edges, deltas)
        for i, e in enumerate(result.edges()):
            print(f"{result.vp.id[e.source()]} --> {result.vp.id[e.target()]} / {result.ep.material[e]}: {result.ep.amount[e]}")
            if result.vp.id[e.source()] == 'Packaging' \
                    and result.vp.id[e.target()] == 'Consumption' \
                    and result.ep.material[e] == 'plastic':
                expected = 5.0 - 0.6017
                self.assertAlmostEqual(result.ep.amount[e], expected, 2)
            elif result.vp.id[e.source()] == 'Oil rig' \
                    and result.vp.id[e.target()] == 'Oil refinery' \
                    and result.ep.material[e] == 'crude oil':
                expected = 20.0 - 0.6017
                self.assertAlmostEqual(result.ep.amount[e], expected, 2)
            elif result.vp.id[e.source()] == 'Oil refinery' \
                    and result.vp.id[e.target()] == 'Production' \
                    and result.ep.material[e] == 'plastic':
                expected = 4.0 - 0.48136
                self.assertAlmostEqual(result.ep.amount[e], expected, 2)
            elif result.vp.id[e.source()] == 'Production' \
                    and result.vp.id[e.target()] == 'Packaging' \
                    and result.ep.material[e] == 'plastic':
                expected = 5.0 - 0.6017
                self.assertAlmostEqual(result.ep.amount[e], expected, 2)
            elif result.vp.id[e.source()] == 'Consumption' \
                    and result.vp.id[e.target()] == 'Burn' \
                    and result.ep.material[e] == 'plastic':
                expected = 3.0 - 0.36102
                self.assertAlmostEqual(result.ep.amount[e], expected, 2)
            elif result.vp.id[e.source()] == 'Consumption' \
                    and result.vp.id[e.target()] == 'Recycling' \
                    and result.ep.material[e] == 'plastic':
                expected = 2.0 - 0.24068
                self.assertAlmostEqual(result.ep.amount[e], expected, 2)
            elif result.vp.id[e.source()] == 'Recycling' \
                    and result.vp.id[e.target()] == 'Production' \
                    and result.ep.material[e] == 'plastic':
                expected = 1.0 - 0.12034
                self.assertAlmostEqual(result.ep.amount[e], expected, 2)
            else:
                self.assertAlmostEqual(result.ep.amount[e],
                                       gw.graph.ep.amount[e], places=2)


    def test_milk_production(self):
        """Reduce milk production between Farm->Packaging

        Results (change in tons):
            Farm --> Packaging -26.0
            Packaging --> Consumption -26.0
            Consumption --> Waste -20.526315789473685
            Consumption --> Waste 2 -5.473684210526315
        """
        plastic = flowmodeltestdata.plastic_package_graph()
        gw = GraphWalker(plastic)
        change = gw.graph.new_edge_property('float')
        gw.graph.edge_properties['change'] = change
        changed = gw.graph.new_edge_property('bool',
                                             vals=[False for e in range(gw.graph.num_edges())])
        gw.graph.edge_properties['changed'] = changed
        include = gw.graph.new_edge_property('bool')
        gw.graph.edge_properties['include'] = include
        bf = gw.graph.new_vertex_property('float',
                                          vals=[1.0 for v in range(gw.graph.num_vertices())])
        gw.graph.vertex_properties['downstream_balance_factor'] = bf
        pe = gw.graph.edge(gw.graph.vertex(0), gw.graph.vertex(1),
                           all_edges=True)  # the 2 edges between Farm and Packaging
        implementation_edges = [e for e in pe
                                if gw.graph.ep.material[e] == 'milk']
        # reduce the milk production by 26.0 tons on the implementation_edge
        deltas = [-26.0]
        # select affected flows
        for i, e in enumerate(gw.graph.edges()):
            # these material flows are affected by the solution
            if gw.graph.ep.material[e] in ['milk', 'human waste', 'other waste']:
                gw.graph.ep.include[e] = True
            else:
                gw.graph.ep.include[e] = False
        result = gw.calculate(implementation_edges, deltas)
        for i, e in enumerate(result.edges()):
            print(f"{result.vp.id[e.source()]} --> {result.vp.id[e.target()]} / {result.ep.material[e]}: {result.ep.amount[e]}")
            if result.vp.id[e.source()] == 'Farm' \
                    and result.vp.id[e.target()] == 'Packaging' \
                    and result.ep.material[e] == 'milk':
                expected = 65.0 - 26.0
                self.assertAlmostEqual(result.ep.amount[e], expected, places=2)
            elif result.vp.id[e.source()] == 'Packaging' \
                    and result.vp.id[e.target()] == 'Consumption' \
                    and result.ep.material[e] == 'milk':
                expected = 65.0 - 26.0
                self.assertAlmostEqual(result.ep.amount[e], expected, places=2)
            elif result.vp.id[e.source()] == 'Consumption' \
                    and result.vp.id[e.target()] == 'Waste' \
                    and result.ep.material[e] == 'human waste':
                expected = 75.0 - 20.526315789473685
                self.assertAlmostEqual(result.ep.amount[e], expected, places=2)
            elif result.vp.id[e.source()] == 'Consumption' \
                    and result.vp.id[e.target()] == 'Waste 2' \
                    and result.ep.material[e] == 'other waste':
                expected = 20.0 - 5.473684210526315
                self.assertAlmostEqual(result.ep.amount[e], expected, places=2)
            else:
                self.assertAlmostEqual(result.ep.amount[e],
                                       gw.graph.ep.amount[e], places=2)


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
        cls.treatment_nonhazardous = Activity.objects.get(nace='E-3821')
        cls.treatment_hazardous = Activity.objects.get(nace='E-3822')
        cls.processing = Activity.objects.get(nace='C-1030')
        cls.pharma_manufacture = Activity.objects.get(nace='C-2110')
        cls.textile_manufacture = Activity.objects.get(nace='C-1399')
        cls.retail_cosmetics = Activity.objects.get(nace='G-4775')
        cls.petroleum_manufacture = Activity.objects.get(nace='C-1920')
        cls.road_transport = Activity.objects.get(nace='H-4941')
        cls.other_transport = Activity.objects.get(nace='H-5229')

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

        def affect_biofuel_chain(solpart):
            '''add affected biofuel flows to given solution part'''
            AffectedFlowFactory(
                origin_activity=self.treatment_nonhazardous,
                destination_activity=self.petroleum_manufacture,
                solution_part=solpart,
                material=self.biofuel
            )
            AffectedFlowFactory(
                origin_activity=self.petroleum_manufacture,
                destination_activity=self.road_transport,
                solution_part=solpart,
                material=self.biofuel
            )
            AffectedFlowFactory(
                origin_activity=self.petroleum_manufacture,
                destination_activity=self.other_transport,
                solution_part=solpart,
                material=self.biofuel
            )
            AffectedFlowFactory(
                origin_activity=self.road_transport,
                destination_activity=self.treatment_hazardous,
                solution_part=solpart,
                material=self.biofuel
            )
            AffectedFlowFactory(
                origin_activity=self.other_transport,
                destination_activity=self.treatment_hazardous,
                solution_part=solpart,
                material=self.biofuel
            )

        ### shift food waste from treatment to processing ###
        ### -> new orange peel flows ###

        restaurants_to_treat = FlowReferenceFactory(
            origin_activity=self.restaurants,
            destination_activity=self.treatment_nonhazardous,
            material=self.food_waste
        )

        retail_to_treat = FlowReferenceFactory(
            origin_activity=self.retail_food,
            destination_activity=self.treatment_nonhazardous,
            material=self.food_waste
        )

        # ToDo: change process?
        shift_to_processing = FlowReferenceFactory(
            destination_activity=self.processing,
            material=self.orange_peel
        )

        # part to shift flows from restaurants
        part1 = SolutionPartFactory(
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

        affect_biofuel_chain(part1)

        # part to shift flows from retail
        part2 = SolutionPartFactory(
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

        affect_biofuel_chain(part2)

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
            destination_activity=self.treatment_nonhazardous,
            material=self.organic_waste,
            waste=1
        )

        # part to append to restaurant-processing flows going to treatment
        part3 = SolutionPartFactory(
            name='append to restaurant->processing -> treatment',
            solution=self.solution,
            flow_reference=rest_to_proc,
            flow_changes=append_treatment,
            scheme=Scheme.APPEND,
            b=0.5,
            priority=priority
        )
        priority += 1

        affect_biofuel_chain(part3)

        # part to append flows to retail-processing flows going to treatment
        part4 = SolutionPartFactory(
            name='append to retail->processing -> treatment',
            solution=self.solution,
            flow_reference=retail_to_proc,
            flow_changes=append_treatment,
            scheme=Scheme.APPEND,
            b=0.5,
            priority=priority
        )
        priority += 1

        affect_biofuel_chain(part4)

        append_textile = FlowReferenceFactory(
            destination_activity=self.textile_manufacture,
            material=self.fiber,
            waste=0
        )

        # part to append to restaurant-processing flows going to textile manu.
        part5 = SolutionPartFactory(
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
        part6 = SolutionPartFactory(
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
        part7 = SolutionPartFactory(
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
            solution_part=part7,
            material=self.essential_oils
        )

        # part to append to retail-processing flows going to pharma
        part8 = SolutionPartFactory(
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
            solution_part=part8,
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
            destination__activity=self.treatment_nonhazardous,
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
            destination__activity=self.treatment_nonhazardous,
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
            destination__activity=self.treatment_nonhazardous
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
            origin__activity=self.treatment_nonhazardous,
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
                               'strategy is not the same as in status quo')

        def assert_balance_factor(activity):
            actors = Actor.objects.filter(activity=activity)
            for actor in actors:
                in_flows = FractionFlow.objects.filter(destination=actor).annotate(
                    strategy_amount=Coalesce('f_strategyfractionflow__amount',
                                             'amount'),
                    statusquo_amount=Case(
                        When(strategy__isnull=False, then=0),
                        default=F('amount')
                    )
                )
                out_flows = FractionFlow.objects.filter(origin=actor).annotate(
                    strategy_amount=Coalesce('f_strategyfractionflow__amount',
                                             'amount'),
                    statusquo_amount=Case(
                        When(strategy__isnull=False, then=0),
                        default=F('amount')
                    )
                )
                if not (out_flows and in_flows):
                    continue
                sq_in = in_flows.aggregate(amount=Sum('statusquo_amount'))['amount']
                sq_out = out_flows.aggregate(amount=Sum('statusquo_amount'))['amount']
                sf_in = in_flows.aggregate(amount=Sum('strategy_amount'))['amount']
                sf_out = out_flows.aggregate(amount=Sum('strategy_amount'))['amount']
                sq_factor = (sq_out / sq_in) if sq_out and sq_in else 1
                sf_factor = (sf_out / sf_in) if sf_out and sf_in else 1
                self.assertAlmostEqual(sq_factor, sf_factor,
                                       msg='the balance factor at actor '
                                       f'{actor} in strategy is not the '
                                       'same as in status quo')

        assert_balance_factor(self.treatment_nonhazardous)
        assert_balance_factor(self.petroleum_manufacture)
        assert_balance_factor(self.road_transport)
        assert_balance_factor(self.other_transport)
        assert_balance_factor(self.treatment_hazardous)

        treat_non_out = FractionFlow.objects.filter(
            origin__activity=self.treatment_nonhazardous).annotate(
                strategy_amount=Coalesce('f_strategyfractionflow__amount',
                                         'amount'))
        treat_haz_in = FractionFlow.objects.filter(
            destination__activity=self.treatment_hazardous).annotate(
                strategy_amount=Coalesce('f_strategyfractionflow__amount',
                                         'amount'))
        treat_non_out_sum = treat_non_out.aggregate(
            sq_amount=Sum('amount'), strat_amount=Sum('strategy_amount'))
        treat_non_out_delta = (treat_non_out_sum['strat_amount'] -
                               treat_non_out_sum['sq_amount'])
        treat_haz_in_sum = treat_haz_in.aggregate(
            sq_amount=Sum('amount'), strat_amount=Sum('strategy_amount'))
        treat_haz_in_delta = (treat_haz_in_sum['strat_amount'] -
                              treat_haz_in_sum['sq_amount'])

        self.assertAlmostEqual(
            treat_non_out_delta * 0.2, treat_haz_in_delta,
            msg=f'change of out-flow sum {treat_non_out_delta} '
            'of non hazardous waste treatment should be 5 '
            f'times the change of in-flow sum {treat_haz_in_delta}'
            'hazardous waste treatment')

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
        # ToDo: count recently added affected flows
        #assert StrategyFractionFlow.objects.count() == (
                #sq_rest_to_treat.count() + sq_retail_to_treat.count() +
                #sq_petroleum_flows.count() + sq_cosmetic_flows.count())
        #assert StrategyFractionFlow.objects.count() == (
            #new_strat_flow_count + affected_petroleum.count())


class StrategyGraphPerformanceTest(MultiplyTestDataMixin,
                                   StrategyGraphTest):
    """The same tests but with bigger data"""

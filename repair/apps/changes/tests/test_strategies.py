from django.test import TestCase
from django.urls import reverse
from test_plus import APITestCase
from django.contrib.gis.geos import Point, MultiPoint, LineString

from repair.tests.test import BasicModelPermissionTest, BasicModelReadTest

from repair.apps.changes.models import (ImplementationQuantity, SolutionPart,
                                        AffectedFlow, Scheme,
                                        ImplementationArea)
from repair.apps.asmfa.models import Actor, Activity, Material
from django.contrib.gis.geos import Polygon, Point, MultiPolygon

from repair.apps.changes.factories import (
    SolutionFactory, StrategyFactory, ImplementationQuestionFactory,
    SolutionPartFactory, SolutionInStrategyFactory,
    FlowReferenceFactory, PossibleImplementationAreaFactory,
    ImplementationAreaFactory
)
from repair.apps.asmfa.factories import (
    ActivityFactory, ActivityGroupFactory, ActorFactory, MaterialFactory,
    Actor2ActorFactory, FractionFlowFactory, KeyflowInCasestudyFactory,
    ProcessFactory, AdministrativeLocationFactory
)
from repair.apps.asmfa.tests.flowmodeltestdata import GenerateBreadToBeerData
from repair.apps.statusquo.models import SpatialChoice

from repair.apps.studyarea.factories import StakeholderFactory
from repair.apps.login.factories import UserInCasestudyFactory


class ModelSolutionInStrategy(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a solution with 3 parts 2 questions
        cls.solution = SolutionFactory()

        question_1 = ImplementationQuestionFactory(
            question="What is the answer to life, the universe and everything?",
            select_values='0.0,3.14,42,1234.4321',
            solution=cls.solution
        )
        question_2 = ImplementationQuestionFactory(
            question="What is 1 + 1?",
            min_value=1,
            max_value=1000,
            step=1,
            solution=cls.solution
        )

        possible_implementation_area_1 = PossibleImplementationAreaFactory(
            solution=cls.solution,
            geom=MultiPolygon(Polygon(((0.0, 0.0), (0.0, 20.0), (56.0, 20.0),
                                       (56.0, 0.0), (0.0, 0.0)))),
            question=("")
        )

        possible_implementation_area_2 = PossibleImplementationAreaFactory(
            solution=cls.solution,
            geom=MultiPolygon(Polygon(((0.0, 0.0), (0.0, 20.0), (56.0, 20.0),
                                       (56.0, 0.0), (0.0, 0.0)))),
            question=("")
        )

        part_1 = SolutionPartFactory(
            solution=cls.solution,
            question=question_1,
            a=0,
            b=1
        )
        part_2 = SolutionPartFactory(
            solution=cls.solution,
            question=question_2
        )

        # new target with new actors
        target_activity = ActivityFactory(name='target_activity')
        for i in range(3):
            ActorFactory(activity=target_activity)

        new_target = FlowReferenceFactory(
            destination_activity=target_activity,
            destination_area=possible_implementation_area_1
        )

        part_new_flow = SolutionPartFactory(
            solution=cls.solution,
            question=question_1,
            flow_changes=new_target
        )

    def test01_quantities(self):
        """Test the new solution strategy"""

        strategy = StrategyFactory()
        solution_in_strategy = SolutionInStrategyFactory(
            solution=self.solution,
            strategy=strategy)

        # there are 3 parts with only 2 different questions ->
        # 2 quantities should be created automatically
        quantities = ImplementationQuantity.objects.all()
        assert quantities.count() == 2

        impl_areas = ImplementationArea.objects.all()
        assert impl_areas.count() == 2


class BreadToBeerSolution(GenerateBreadToBeerData):
    """Define the Solution for the Bread to Beer case"""

    @classmethod
    def setUpClass(cls):
        """Solution definition"""
        super().setUpClass()
        cls.solution = SolutionFactory(name='Bread to Beer')

        cls.beer_question = ImplementationQuestionFactory(
            question=("How much of the incinerated bread is sent to the Brewery?"),
            solution=cls.solution,
            min_value=0,
            max_value=1,
            is_absolute=False
        )

        ## Solution Parts ##
        brewing_activity = Activity.objects.filter(name='Brewery', nace='A-0000')
        household_activity = Activity.objects.filter(name='Household', nace='A-0001')
        incinerator_activity = Activity.objects.filter(name='Incineration', nace='C-0011')
        farming_activity = Activity.objects.filter(name='Farming', nace='C-0010')
        bread = Material.objects.filter(name='bread', keyflow=cls.keyflow)
        barley = Material.objects.filter(name='barley', keyflow=cls.keyflow)

        implementation = FlowReferenceFactory(
            origin_activity=household_activity[0],
            destination_activity=incinerator_activity[0],
            material=bread[0]
        )

        shift = FlowReferenceFactory(
            destination_activity=brewing_activity[0]
        )

        cls.bread_to_brewery = SolutionPartFactory(
            solution=cls.solution,
            documentation='Bread goes to Brewery instead of Incineration',
            question=cls.beer_question,
            flow_reference=implementation,
            flow_changes=shift,
            scheme=Scheme.SHIFTDESTINATION,

            a = 1,
            b = 0,

            priority=1
        )

        ## Affected flows ##
        AffectedFlow(origin_activity=farming_activity[0],
                     destination_activity=brewing_activity[0],
                     material=barley[0],
                     solution_part=cls.bread_to_brewery)


class BreadToBeerSolutionTest(BreadToBeerSolution):
    """Test the Solution definition for the Bread to Beer case"""

    def test_01_implementation(self):

        user = UserInCasestudyFactory(casestudy=self.keyflow.casestudy,
                                      user__user__username='Hans Norbert')
        strategy = StrategyFactory(keyflow=self.keyflow, user=user)
        implementation = SolutionInStrategyFactory(
            solution=self.solution, strategy=strategy)

        answer = ImplementationQuantity(question=self.beer_question,
                                        implementation=implementation,
                                        value=1)


class ApplyStrategyTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        ### Modeling the FUNGUS solution and the status quo it is based on ###

        cls.keyflow = KeyflowInCasestudyFactory()

        ##  Materials ##

        dummy_mat_1 = MaterialFactory(keyflow=cls.keyflow)
        dummy_mat_2 = MaterialFactory(keyflow=cls.keyflow)
        wool = MaterialFactory(name='wool insulation',
                                          keyflow=cls.keyflow)
        fungus = MaterialFactory(name='fungus insulation',
                                            keyflow=cls.keyflow)
        # no idea about the processes, but the process of wool-insulation flow
        # to E-3821 is supposed to be different to the fungus-insulation one
        dummy_process = ProcessFactory(name='process')
        compost = ProcessFactory(name='compost')

        ## Activities and Activity groups ##

        group_A = ActivityGroupFactory(name='A', code='A', keyflow=cls.keyflow)
        group_C = ActivityGroupFactory(name='C', code='C', keyflow=cls.keyflow)
        group_E = ActivityGroupFactory(name='E', code='E', keyflow=cls.keyflow)
        group_F = ActivityGroupFactory(name='F', code='F', keyflow=cls.keyflow)
        group_V = ActivityGroupFactory(name='V', code='V', keyflow=cls.keyflow)
        dummy_group = ActivityGroupFactory(keyflow=cls.keyflow)

        growing_activity = ActivityFactory(
            name='A-0116 Growing of fibre crops',
            nace='A-0116', activitygroup=group_A)
        manufacture_activity = ActivityFactory(
            name='C-2399 Manufacture of non-metallic mineral products',
            nace='C-2399', activitygroup=group_C)
        collection_activity = ActivityFactory(
            name='E-3819 Collection of non-hazardous waste',
            nace='E-3819', activitygroup=group_E)
        treatment_activity = ActivityFactory(
            name='E-3821 Treatment and disposal of non-hazardous waste',
            nace='E-3821', activitygroup=group_E)
        building_activity = ActivityFactory(
            name='F-4110 Development of building projects',
            nace='F-4110', activitygroup=group_E)
        consumption_activity = ActivityFactory(
            name='V-0000 Consumption in households',
            nace='V-0000', activitygroup=group_V)
        dummy_activity_1 = ActivityFactory(activitygroup=dummy_group)
        dummy_activity_2 = ActivityFactory(activitygroup=dummy_group)

        ## Actors ##

        # random households
        for i in range(100):
            ActorFactory(name='household{}'.format(i),
                         activity=consumption_activity)

        for i in range(2):
            building_dev = ActorFactory(name='buildingdev{}'.format(i),
                                        activity=building_activity)
            # this activity is set as spatial choice in the following solution
            # parts -> they have to be geolocated (just putting it somewhere)
            # Note CF: geolocate the other models as well?
            location = AdministrativeLocationFactory(
                actor=building_dev, geom=Point(x=5, y=52))

        collection_insulation = ActorFactory(name='collection',
                                             activity=collection_activity)

        manufacturer = ActorFactory(name='manufacturer'.format(i),
                                    activity=manufacture_activity)

        # put some dummy actors into the dummy activities
        for i in range(10):
            ActorFactory(activity=dummy_activity_1)
            ActorFactory(activity=dummy_activity_2)

        treatment_insulation = ActorFactory(name='disposal',
                                            activity=treatment_activity)
        cls.treatment_compost = ActorFactory(name='compost',
                                             activity=treatment_activity)

        # putting the fungus farms into "growing fibre crops" lacking better
        # knowledge
        fungus_input = ActorFactory(name='chungus',
                                    activity=growing_activity)
        cls.fungus_farm_1 = ActorFactory(name='fungus1',
                                         activity=growing_activity)
        cls.fungus_farm_2 = ActorFactory(name='fungus2',
                                         activity=growing_activity)

        ## status quo flows and stocks ##

        # making stuff up going into the fungus farm
        FractionFlowFactory(origin=fungus_input, destination=cls.fungus_farm_1,
                            material=dummy_mat_1,
                            amount=20)
        FractionFlowFactory(origin=fungus_input, destination=cls.fungus_farm_2,
                            material=dummy_mat_2,
                            amount=10)

        # fungus stock to possibly derive from
        # (Note CF: is there a stock? better: put the output to the treatment)
        FractionFlowFactory(origin=cls.fungus_farm_1, material=fungus,
                            amount=10)
        FractionFlowFactory(origin=cls.fungus_farm_2, material=fungus,
                            amount=10)
        # (Note CF: set stocks as affected flows?)

        households = Actor.objects.filter(activity=consumption_activity)
        # every household gets same share of 200,000 t/y activity stock
        stock_share = 200000 / len(households)
        # Note CF: no idea how much should go in per year
        input_share = 10 / len(households)
        builders = Actor.objects.filter(activity=building_activity)
        step = len(households) / len(builders)

        # household stock and input
        for i, household in enumerate(households):
            # stock
            FractionFlowFactory(origin=household, material=wool,
                                amount=stock_share)
            # equally distribute the inputs from the building developers
            builder = builders[int(i/step)]
            FractionFlowFactory(origin=builder, destination=household,
                                material=wool,
                                amount=input_share)

        input_share = 5 / len(builders)  # Note CF: how much goes in?
        # inputs and outputs of builders
        for builder in builders:
            # from manufacturer
            FractionFlowFactory(origin=manufacturer,
                                destination=builder,
                                material=wool,
                                amount=input_share)
            # to collection
            FractionFlowFactory(origin=builder,
                                destination=collection_insulation,
                                material=wool,
                                amount=1)
            # to treatment
            FractionFlowFactory(origin=builder,
                                destination=treatment_insulation,
                                material=wool,
                                amount=3)

        # collection to treatment
        FractionFlowFactory(origin=collection_insulation,
                            destination=treatment_insulation,
                            material=wool,
                            amount=2)

        # manufacturer to treatment
        FractionFlowFactory(origin=manufacturer,
                            destination=treatment_insulation,
                            material=wool,
                            amount=2)

        ## solution definition ##

        cls.solution = SolutionFactory(name='Fungus Isolation')

        cls.fungus_question = ImplementationQuestionFactory(
            question=("How many tonnes per year of fungus should be used as "
                      "insulation material when developing new "
                      "living quarters?"),
            solution=cls.solution,
            min_value=0,
            is_absolute=True # Note CF: is it?
        )

        cls.possible_implementation_area = PossibleImplementationAreaFactory(
            solution=cls.solution,
            geom=MultiPolygon(Polygon(((0.0, 0.0), (0.0, 20.0), (56.0, 20.0),
                                       (56.0, 0.0), (0.0, 0.0)))),
            question=("Where are the facilities for composting "
                      "the fungus located?")
        )

        ## solution parts ##

        # the new flow based on flows from c-2399 to f-4110
        # Note CF: optional it could also be derived from flows out of the farms

        implementation = FlowReferenceFactory(
            origin_activity=manufacture_activity,
            destination_activity=building_activity,
            material=wool
        )

        shift = FlowReferenceFactory(
            origin_activity=growing_activity,
            material=fungus
        )

        cls.new_fungus_insulation = SolutionPartFactory(
            solution=cls.solution,
            question=cls.fungus_question,
            flow_reference=implementation,
            flow_changes=shift,
            scheme=Scheme.SHIFTORIGIN,
            a = 1,
            b = 0,
            priority=1
        )

        # the new flow based on flows from c-2399 to f-4110
        # Note CF: optional it could also be derived from flows out of the farms

        implementation = FlowReferenceFactory(
            origin_activity=consumption_activity,
            destination_activity=None,
            process=dummy_process,
            material=wool
        )

        # origin actually stays the same but there is no way to shift without
        # referring to either new destination or origin
        shift = FlowReferenceFactory(
            origin_activity=consumption_activity,
            material=fungus
        )

        new_fungus_stock = SolutionPartFactory(
            solution=cls.solution,
            question=cls.fungus_question,
            flow_reference=implementation,
            flow_changes=shift,
            scheme=Scheme.SHIFTORIGIN,
            a = 1,
            b = 0,
            priority=2
        )

        # new flow from F-4110 development to E-3821 treatment
        # Note CF: deriving it from existing F4110 to E3821, just guessing

        implementation = FlowReferenceFactory(
            origin_activity=building_activity,
            destination_activity=treatment_activity,
            material=wool,
            process=dummy_process
        )

        # actually both activities stay the same
        shift = FlowReferenceFactory(
            origin_activity=building_activity,
            destination_activity=treatment_activity,
            material=fungus,
            process=compost,
            destination_area=cls.possible_implementation_area
        )

        cls.new_building_disposal = SolutionPartFactory(
            solution=cls.solution,
            # Note CF: i guess we need different numbers than asked for in this
            # question, or do we even need a question??
            question=cls.fungus_question,
            flow_reference=implementation,
            flow_changes=shift,
            scheme=Scheme.SHIFTDESTINATION,
            a = 1,
            b = 0,
            priority=3
        )

        # new flow from fungus farms to E-3821 treatment
        # Note CF: most likely this should already be modelled in the status quo
        # deriving it from fungus stock

        implementation = FlowReferenceFactory(
            origin_activity=growing_activity,
            destination_activity=None,
            process=compost,
            material=fungus
        )

        # origin actually stays the same but there is no way to shift without
        # referring to either new destination or origin
        shift = FlowReferenceFactory(
            destination_activity=treatment_activity,
            destination_area=cls.possible_implementation_area,
            material=fungus
        )

        # Note CF: reduce existing implementation flow?

        new_fungus_disposal = SolutionPartFactory(
            solution=cls.solution,
            # Note CF: is there a question???
            question=None,
            flow_reference=implementation,
            flow_changes=shift,
            scheme=Scheme.SHIFTDESTINATION,

            a = 1,
            b = 0,

            priority=4
        )

        ## affected flows ##

        # Note CF: poor pull leader has to define the affected flows for
        # every part, just taking the same ones for all parts
        # (marking the implementation flows as well, i guess that doesn't matter)
        # B: who cares about the pull leader?!

        parts = [cls.new_fungus_insulation,
                 new_fungus_stock, cls.new_building_disposal,
                 new_fungus_disposal]

        for part in parts:
            # F-4110 to V-0000
            AffectedFlow(origin_activity=building_activity,
                         destination_activity=consumption_activity,
                         material=wool, solution_part=part)

            # Note CF: insulation stock of V-0000 affected as well?

            # inputs of fungus farm, origin and destination are in same activity
            # Note CF: might not be this way in reality, maybe inputs come from
            # different activity? stock missing
            AffectedFlow(origin_activity=growing_activity,
                         destination_activity=growing_activity,
                         material=dummy_mat_1, solution_part=part)
            AffectedFlow(origin_activity=growing_activity,
                         destination_activity=growing_activity,
                         material=dummy_mat_2, solution_part=part)

            # F-4110 to E-3821
            AffectedFlow(origin_activity=building_activity,
                         destination_activity=treatment_activity,
                         material=wool, solution_part=part)
            # F-4110 to E-3819
            AffectedFlow(origin_activity=building_activity,
                         destination_activity=collection_activity,
                         material=wool, solution_part=part)

            # C-2399 to F-4110
            AffectedFlow(origin_activity=manufacture_activity,
                         destination_activity=building_activity,
                         material=wool, solution_part=part)

            # E-3819 to E-3821
            AffectedFlow(origin_activity=collection_activity,
                         destination_activity=treatment_activity,
                         material=wool, solution_part=part)


    def test_01_implementation(self):

        ## implement the solution as a user would ##

        user = UserInCasestudyFactory(casestudy=self.keyflow.casestudy,
                                      user__user__username='Hans Herbert')
        strategy = StrategyFactory(keyflow=self.keyflow, user=user)
        implementation = SolutionInStrategyFactory(
            solution=self.solution, strategy=strategy)

        implementation_area = ImplementationAreaFactory(
            implementation=implementation,
            geom=MultiPolygon(Polygon(((0.0, 0.0), (0.0, 20.0), (56.0, 20.0),
                                       (56.0, 0.0), (0.0, 0.0)))),
            possible_implementation_area=self.possible_implementation_area
        )

        # answer the question
        # Note CF: the diagram says 250 * 5 cubic meters, don't know what fungus
        # insulation weighs
        answer = ImplementationQuantity(question=self.fungus_question,
                                        implementation=implementation,
                                        value=25)

        # ToDo: asserts


class SolutionInStrategyInCasestudyTest(BasicModelPermissionTest, APITestCase):

    casestudy = 17
    keyflow = 23
    user = 20
    strategy = 30
    solution = 20
    solutioncategory = 56
    solution_strategy = 40

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solution_url = cls.baseurl + \
            reverse('solution-detail',
                    kwargs=dict(casestudy_pk=cls.casestudy,
                                keyflow_pk=cls.keyflow,
                                pk=cls.solution))
        cls.strategy_url = cls.baseurl + \
            reverse('strategy-detail',
                    kwargs=dict(casestudy_pk=cls.casestudy,
                                keyflow_pk=cls.keyflow,
                                pk=cls.strategy))
        cls.post_urls = [cls.solution_url, cls.strategy_url]
        cls.sol_set = []
        cls.url_key = "solutioninstrategy"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           strategy_pk=cls.strategy,
                           keyflow_pk=cls.keyflow)
        cls.url_pk = dict(pk=cls.solution)
        cls.post_data = dict(solution=cls.solution,
                             strategy=cls.strategy_url)
        cls.put_data = dict(solution=cls.solution,
                            strategy=cls.strategy_url)
        cls.patch_data = dict(solution=cls.solution,
                              strategy=cls.strategy_url)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.obj = SolutionInStrategyFactory(
            solution__id=cls.solution,
            strategy__user=cls.uic,
            strategy__id=cls.strategy,
            strategy__keyflow=cls.kic_obj,
            solution__solution_category__id=cls.solutioncategory,
            solution__solution_category__keyflow=cls.kic_obj,
            id=cls.solution_strategy)

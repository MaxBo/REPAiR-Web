from django.test import TestCase
from django.urls import reverse
from test_plus import APITestCase
from django.contrib.gis.geos import Point, MultiPoint, LineString

from repair.tests.test import BasicModelPermissionTest, BasicModelReadTest

from repair.apps.changes.models import (ImplementationQuantity, SolutionPart,
                                        ActorInSolutionPart)
from repair.apps.asmfa.models import Actor

from repair.apps.changes.factories import (
    SolutionFactory,
    StrategyFactory,
    ImplementationQuestionFactory,
    SolutionPartFactory,
    SolutionInStrategyFactory,
)
from repair.apps.asmfa.factories import (
    ActivityFactory,
    ActorFactory
)

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

        part_new_flow = SolutionPartFactory(
            solution=cls.solution,
            question=question_1,
            implements_new_flow=True,
            keep_origin=True,
            new_target_activity=target_activity,
            map_request="pick an actor"
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

    def test02_target_actor(self):
        """Test the new solution strategy"""

        strategy = StrategyFactory()
        solution_in_strategy = SolutionInStrategyFactory(
            solution=self.solution,
            strategy=strategy)

        new_flow_parts = SolutionPart.objects.filter(
            solution=self.solution, implements_new_flow=True)

        for part in new_flow_parts:
            target = part.new_target_activity
            actors = Actor.objects.filter(activity=target)
            target_actor = ActorInSolutionPart(
                solutionpart=part, actor=actors.first(),
                implementation=solution_in_strategy
            )
            # ToDo: test sth meaningful here?


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
                                solutioncategory_pk=cls.solutioncategory,
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

    def setUp(self):
        super().setUp()
        self.obj = SolutionInStrategyFactory(
            solution__user=self.uic,
            solution__solution_category__user=self.uic,
            solution__id=self.solution,
            strategy__user=self.uic,
            strategy__id=self.strategy,
            strategy__keyflow=self.kic,
            solution__solution_category__id=self.solutioncategory,
            solution__solution_category__keyflow=self.kic,
            id=self.solution_strategy)

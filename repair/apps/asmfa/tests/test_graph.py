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
from repair.apps.changes.models import ImplementationQuantity, ActorInSolutionPart
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
    stakeholdercategoryid = 48
    stakeholderid = 21
    strategyid = 1
    materialname = 'wool insulation'

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


        stakeholder = StakeholderFactory(
            id=self.stakeholderid,
            stakeholder_category__id=self.stakeholdercategoryid,
            stakeholder_category__casestudy=self.uic.casestudy,
        )
        user = UserInCasestudyFactory(casestudy=self.kic.casestudy,
                                      user__user__username='Hans Norbert')
        ## generate a new strategy
        self.strategy = StrategyFactory(id=self.strategyid,
                                   keyflow=self.kic,
                                   user=user,
                                   name='Test Strategy')

        # Create a solution with 3 parts 2 questions
        self.solution1 = SolutionFactory(name='Solution 1')

        question1 = ImplementationQuestionFactory(
            question="Which percentage should be shifted to new flow?",
            is_absolute=False,
            #select_values='0.0,3.14,42,1234.43',
            solution=self.solution1
        )
        question2 = ImplementationQuestionFactory(
            question="What is 1 + 1?",
            min_value=1,
            max_value=1000,
            step=1,
            solution=self.solution1
        )

        # new origin with new actor
        origin_activity = ActivityFactory(name='origin_activity')
        self.origin_actor = ActorFactory(name='origin_actor',
                                         activity=origin_activity)
        AdministrativeLocationFactory(
            actor=self.origin_actor,
            geom=Point(x=10, y=10, srid=4326)
        )

        # old target with actor
        old_destination_activity = ActivityFactory(
            name='old_destination_activity_activity')
        old_destination_actor = ActorFactory(name='old_destination_actor',
                                             activity=old_destination_activity)
        AdministrativeLocationFactory(
            actor=old_destination_actor,
            geom=Point(x=10.1, y=10.1, srid=4326)
        )

        # new target with new actor
        new_destination_activity = ActivityFactory(name='target_activity')
        self.new_destination_actor = ActorFactory(
            name='new_destination_actor',
            activity=new_destination_activity
        )
        AdministrativeLocationFactory(
            actor=self.new_destination_actor,
            geom=Point(x=12, y=12, srid=4326)
        )

        # actor 11
        actor11 = ActorFactory(name='Actor11',
                               activity=origin_activity)
        AdministrativeLocationFactory(
            actor=actor11,
            geom=Point(x=10.5, y=10, srid=4326)
        )
        # actor 12
        actor12 = ActorFactory(name='Actor12',
                               activity=new_destination_activity)
        AdministrativeLocationFactory(
            actor=actor12,
            geom=Point(x=11, y=10, srid=4326)
        )

        # new material
        wool = MaterialFactory(name=self.materialname,
                               keyflow=self.kic)

        part_new_flow = SolutionPartFactory(
            solution=self.solution1,
            implementation_flow_origin_activity=origin_activity,
            implementation_flow_destination_activity=old_destination_activity,
            implementation_flow_material=wool,
            #implementation_flow_process=,
            question=question1,
            a=1.0,
            b=0,
            implements_new_flow=True,
            keep_origin=True,
            new_target_activity=new_destination_activity,
            map_request="pick an actor"
        )

        # create fraction flow
        statusquo_flow1 = FractionFlowFactory(
            origin=self.origin_actor,
            destination=old_destination_actor,
            material=wool,
            amount=1000,
            keyflow=self.kic
        )
        # create fraction flow 2
        statusquo_flow2 = FractionFlowFactory(
            origin=actor11,
            destination=old_destination_actor,
            material=wool,
            amount=11000,
            keyflow=self.kic
        )

        implementation_area = Polygon(((0.0, 0.0), (0.0, 20.0), (56.0, 20.0),
                                       (56.0, 0.0), (0.0, 0.0)))
        solution_in_strategy1 = SolutionInStrategyFactory(
            solution=self.solution1, strategy=self.strategy,
            geom=GeometryCollection(implementation_area), priority=0)

        # quantities are auto-generated, don't create new ones!
        answer = ImplementationQuantity.objects.get(
            question=question1,
            implementation=solution_in_strategy1
        )
        answer.value = 0.2
        answer.save()
        #answer = ImplementationQuantityFactory(
            #question=question1,
            #implementation=solution_in_strategy1,
            #value=1.0)

        picked_destination = ActorInSolutionPartFactory(
            implementation=solution_in_strategy1,
            actor=self.new_destination_actor,
            solutionpart=part_new_flow
        )
        # create AffectedFlow
        affected = AffectedFlowFactory(
            solution_part=part_new_flow,
            origin_activity=origin_activity,
            destination_activity=new_destination_activity,
            material=wool
        )

        #self.solution2 = SolutionFactory(name='Solution 2')
        #solution_in_strategy2 = SolutionInStrategyFactory(
            #solution=self.solution2, strategy=self.strategy,
            #priority=1)

        base_graph = BaseGraph(self.kic, tag='test')
        base_graph.remove()
        base_graph.build()
        base_graph.save()


    def test_graph(self):
        return
        self.graph = StrategyGraph(self.strategy, tag='test')
        # delete stored graph file to test creation of data
        self.graph.remove()
        self.graph.build()

        # two existing flows and two new flows shifted from them
        assert len(FractionFlow.objects.all()) == 4

        flows = FractionFlow.objects.filter(
            origin=self.origin_actor).annotate(
            actual_amount=Coalesce('f_strategyfractionflow__amount', 'amount'))

        # original one and shifted one
        assert len(flows) == 2
        # new flow
        ff = flows.get(strategy=self.strategy)
        assert ff.material.name == self.materialname
        assert ff.destination == self.new_destination_actor

        # ToDo: rewrite tests, just halfing every shifted flow is not what is
        #  supposed to happen but having new flows whose amounts are factor
        # * original amount and a reduction of 1 - factor at the original flows

        return

        #flow is split to new destination thus devided by 2
        assert ff.actual_amount == 500

        # there is 1 strategyflows that sets the amount to 0 for the
        # implementation_flow; no other strategyflows because we didnt include
        # the flows in AffectedFlows
        assert len(StrategyFractionFlow.objects.all()) == 1
        strategyflows = StrategyFractionFlow.objects.filter(
            fractionflow__id=1,
            material__name=self.materialname
        )
        assert len(strategyflows) == 1
        assert strategyflows[0].amount == 0.0

        # test again but now with loading the stored graph
        self.graph.build()

        assert len(FractionFlow.objects.all()) == 4

        flows = FractionFlow.objects.filter(
            origin_id=self.actor_originid,
            destination_id=self.actor_new_targetid).annotate(
            actual_amount=Coalesce('f_strategyfractionflow__amount', 'amount'))

        assert len(flows) == 1
        ff = flows[0]
        assert ff.material.name == self.materialname
        assert ff.destination.id == self.actor_new_targetid
        #flow is split to new destination thus devided by 2
        assert ff.actual_amount == 500

        # there is 1 strategyflows that sets the amount to 0 for the
        # implementation_flow; no other strategyflows because we didnt include
        # the flows in AffectedFlows
        assert len(StrategyFractionFlow.objects.all()) == 1
        strategyflows = StrategyFractionFlow.objects.filter(
            fractionflow__id=1,
            material__name=self.materialname
        )
        assert len(strategyflows) == 1
        assert strategyflows[0].amount == 0.0

    def test_select_closest_actor(self):
        #actors_in_solution = ActorInSolutionPart.objects.filter(
            #solutionpart=solution_part,
            #implementation=implementation)

        #assert len(actors_in_solution) > 0

        actors_in_solution = Actor.objects.all()
        possible_target_actors = Actor.objects.all()
        target_actor = StrategyGraph.find_closest_actor(
            actors_in_solution,
            possible_target_actors)
        assert target_actor.name == 'old_destination_actor'
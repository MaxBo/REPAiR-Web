import os
from test_plus import APITestCase
from repair.apps.asmfa.graphs.graph import BaseGraph, StrategyGraph
from repair.tests.test import LoginTestCase, AdminAreaTest

from repair.apps.asmfa.factories import (ActorFactory,
                                         ActivityFactory,
                                         ActivityGroupFactory,
                                         MaterialFactory,
                                         FractionFlowFactory
                                        )
from repair.apps.changes.factories import (StrategyFactory,
                                           SolutionInStrategyFactory,
                                           SolutionCategoryFactory,
                                           SolutionFactory,
                                           SolutionPartFactory,
                                           ImplementationQuestionFactory,
                                           ImplementationQuantityFactory,
                                           AffectedFlowFactory
                                        )
from repair.apps.asmfa.models import FractionFlow
from repair.apps.studyarea.factories import StakeholderFactory
from repair.apps.login.factories import UserInCasestudyFactory
from django.contrib.gis.geos import Polygon, Point, GeometryCollection
from django.db.models.functions import Coalesce

#class GraphTest(LoginTestCase, APITestCase):

    #@classmethod
    #def setUpClass(cls):
        #super().setUpClass()

    #def setUp(self):
        #super().setUp()
        #self.activitygroup1 = ActivityGroupFactory(name='MyGroup',
                                                   #keyflow=self.kic)
        #self.activitygroup2 = ActivityGroupFactory(name='AnotherGroup',
                                                   #keyflow=self.kic)
        #self.activity1 = ActivityFactory(nace='NACE1',
                                         #activitygroup=self.activitygroup1)
        #self.activity2 = ActivityFactory(nace='NACE2',
                                         #activitygroup=self.activitygroup1)
        #self.activity3 = ActivityFactory(nace='NACE1',
                                         #activitygroup=self.activitygroup1)
        #self.activity4 = ActivityFactory(nace='NACE3',
                                         #activitygroup=self.activitygroup2)

    #def test_graph(self):
        #self.graph = BaseGraph(self.kic)

class StrategyGraphTest(LoginTestCase, APITestCase):
    stakeholdercategoryid = 48
    stakeholderid = 21
    strategyid = 1
    actor_originid = 1
    actor_old_targetid = 2
    actor_new_targetid = 3
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
        
        
        stakeholder = StakeholderFactory(id=self.stakeholderid, 
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
            question="What is the answer to life, the universe and everything?",
            min_value=0.0,
            max_value=10000.0,
            step=0.01,
            select_values='0.0,3.14,42,1234.43',
            solution=self.solution1
        )
        question2 = ImplementationQuestionFactory(
            question="What is 1 + 1?",
            min_value=1,
            max_value=1000,
            step=1,
            solution=self.solution1
        )

        #self.solutionpart1 = SolutionPartFactory(
            #solution=self.solution1,
            #question=question1,
            #a=0,
            #b=1
        #)
        #self.solutionpart2 = SolutionPartFactory(
            #solution=self.solution1,
            #question=question2
        #)
        
        # new origin with new actor
        origin_activity = ActivityFactory(name='origin_activity')
        origin_actor = ActorFactory(id=self.actor_originid,
                                    name='origin_actor',
                                    activity=origin_activity)

        # old target with actor
        old_destination_activity = ActivityFactory(name='old_destination_activity_activity')
        old_destination_actor = ActorFactory(id=self.actor_old_targetid,
                                             name='old_destination_actor',
                                             activity=old_destination_activity)
        
        # new target with new actor
        new_destination_activity = ActivityFactory(name='target_activity')
        new_destination_actor = ActorFactory(id=self.actor_new_targetid,
                                             name='new_destination_actor',
                                             activity=new_destination_activity)
        
        # actor 11
        actor11 = ActorFactory(id=11, name='Actor11', activity=origin_activity)
        # actor 12
        actor12 = ActorFactory(id=12, name='Actor12', activity=new_destination_activity)
                
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
            b=1.0,
            implements_new_flow=True,
            keep_origin=True,
            new_target_activity=new_destination_activity,
            map_request="pick an actor"
        )
        
        # create fraction flow
        new_flow = FractionFlowFactory(origin=origin_actor, 
                                destination=old_destination_actor,
                                material=wool,
                                amount=1,
                                strategy=self.strategy,
                                keyflow=self.kic
                                )
        # create fraction flow 2
        new_flow2 = FractionFlowFactory(origin=actor11, 
                                destination=actor12,
                                material=wool,
                                amount=11,
                                strategy=self.strategy,
                                keyflow=self.kic
                                )        
        
        implementation_area = Polygon(((0.0, 0.0), (0.0, 20.0), (56.0, 20.0),
                                       (56.0, 0.0), (0.0, 0.0)))        
        solution_in_strategy1 = SolutionInStrategyFactory(
            solution=self.solution1, strategy=self.strategy,
            geom=GeometryCollection(implementation_area), priority=0)
        answer = ImplementationQuantityFactory(question=question1,
                                        implementation=solution_in_strategy1,
                                        value=1.0)
        
        # create AffectedFlow
        affected = AffectedFlowFactory(solution_part=part_new_flow,
                                       origin_activity=origin_activity,
                                       destination_activity=new_destination_activity,
                                       material=wool)
        
        #self.solution2 = SolutionFactory(name='Solution 2')
        #solution_in_strategy2 = SolutionInStrategyFactory(
            #solution=self.solution2, strategy=self.strategy,
            #priority=1)
        
    def test_graph(self):
        self.graph = StrategyGraph(self.strategy)
        # delete stored graph file to test creation of data
        if self.graph.exists:
            os.remove(self.graph.filename)
        
        self.graph.build()
        
        flows = FractionFlow.objects.filter(origin_id=self.actor_originid,
                                            destination_id=self.actor_new_targetid).annotate(
            actual_amount=Coalesce('f_strategyfractionflow__amount', 'amount'))
        assert len(flows) == 1
        ff = flows[0]
        assert ff.material.name == self.materialname
        assert ff.destination.id == self.actor_new_targetid
        print("amount")
        print(ff.amount)
        print("actual_amount")
        print(ff.actual_amount)
        assert ff.actual_amount == 2.0
        
        # test again but now with loading the stored graph
        self.graph.build()

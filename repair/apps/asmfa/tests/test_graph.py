
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
                                           ImplementationQuestionFactory
                                        )
from repair.apps.changes.models import ImplementationQuantity
from repair.apps.studyarea.factories import StakeholderFactory
from repair.apps.login.factories import UserInCasestudyFactory
from django.contrib.gis.geos import Polygon, Point, GeometryCollection

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
            select_values='0.0,3.14,42,1234.4321',
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
        origin_actor = ActorFactory(activity=origin_activity)

        # new target with new actors
        target_activity = ActivityFactory(name='target_activity')
        destination_actor = ActorFactory(activity=target_activity)
        
        # new material
        wool = MaterialFactory(name='wool insulation', 
                               keyflow=self.kic)

        part_new_flow = SolutionPartFactory(
            solution=self.solution1,
            implementation_flow_origin_activity=origin_activity,
            implementation_flow_destination_activity=target_activity,
            implementation_flow_material=wool,
            #implementation_flow_process=,
            question=question1,
            a=1,
            b=1,
            implements_new_flow=True,
            keep_origin=True,
            new_target_activity=target_activity,
            map_request="pick an actor"
        )
        
        # TODO T: create fraction flows
        new_flow = FractionFlowFactory(origin=origin_actor, 
                                destination=destination_actor,
                                material=wool,
                                #composition_name=,
                                #nace=,
                                amount=1,
                                strategy=self.strategy
                                )        
        
        implementation_area = Polygon(((0.0, 0.0), (0.0, 20.0), (56.0, 20.0),
                                       (56.0, 0.0), (0.0, 0.0)))        
        solution_in_strategy1 = SolutionInStrategyFactory(
            solution=self.solution1, strategy=self.strategy,
            geom=GeometryCollection(implementation_area), priority=0)
        answer = ImplementationQuantity(question=question1,
                                        implementation=solution_in_strategy1,
                                        value=1)
        
        self.solution2 = SolutionFactory(name='Solution 2')
        solution_in_strategy2 = SolutionInStrategyFactory(
            solution=self.solution2, strategy=self.strategy,
            priority=1)
        
    def test_graph(self):
        self.graph = StrategyGraph(self.strategy)
        self.graph.build()

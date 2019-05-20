# -*- coding: utf-8 -*-

from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status
from repair.tests.test import BasicModelPermissionTest, LoginTestCase
from repair.apps.asmfa.models import Material
from repair.apps.asmfa.factories import (Actor2ActorFactory,
                                         ActorFactory,
                                         CompositionFactory,
                                         MaterialFactory,
                                         )
from repair.apps.statusquo.factories import (FlowIndicatorFactory,
                                             IndicatorFlowFactory,
                                             )
from repair.apps.studyarea.factories import (AreaFactory,
                                             )
from repair.apps.statusquo.views import ComputeIndicator

class FlowIndicatorTest(BasicModelPermissionTest, APITestCase):

    casestudy = 17
    area_id1 = 1
    area_id2 = 2
    actor_id1 = 1
    actor_id2 = 2
    actor_id3 = 3
    actor_id4 = 4
    actor_id5 = 5
    flow_id1 = 1
    flow_id2 = 2
    flow_id3 = 3
    flow_id4 = 4
    flow_id5 = 5
    flow_id6 = 6
    indicatorflow_ida = 1
    indicatorflow_idb = 2
    flowindicator_id = 1
    keyflow_id1 = 1

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "flowindicator"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.kic.id)
        cls.url_pk = dict(pk=cls.flowindicator_id)

    def setUp(self):
        super().setUp()
        self.area1 = AreaFactory(id=self.area_id1,
                                 )
        self.area2 = AreaFactory(id=self.area_id2,
                                     )
        self.actor1 = ActorFactory(id=self.actor_id1)
        self.actor2 = ActorFactory(id=self.actor_id2)
        self.actor3 = ActorFactory(id=self.actor_id3)
        self.actor4 = ActorFactory(id=self.actor_id4)
        self.actor5 = ActorFactory(id=self.actor_id5)
        self.composition1 = CompositionFactory()
        self.flow1 = Actor2ActorFactory(id=self.flow_id1,
                                        keyflow=self.kic,
                                        composition=self.composition1,
                                        origin=self.actor1,
                                        destination=self.actor2)
        self.flow2 = Actor2ActorFactory(id=self.flow_id2,
                                        keyflow=self.kic,
                                        composition=self.composition1,
                                        origin=self.actor2,
                                        destination=self.actor3
                                        )
        self.flow3 = Actor2ActorFactory(id=self.flow_id3,
                                        keyflow=self.kic,
                                        composition=self.composition1,
                                        origin=self.actor3,
                                        destination=self.actor5)
        self.flow4 = Actor2ActorFactory(id=self.flow_id4,
                                        keyflow=self.kic,
                                        composition=self.composition1,
                                        origin=self.actor5,
                                        destination=self.actor4)
        self.flow5 = Actor2ActorFactory(id=self.flow_id5,
                                        keyflow=self.kic,
                                        composition=self.composition1,
                                        origin=self.actor5,
                                        destination=self.actor3)
        self.flow6 = Actor2ActorFactory(id=self.flow_id6,
                                        keyflow=self.kic,
                                        composition=self.composition1,
                                        origin=self.actor1,
                                        destination=self.actor3)
        self.material1 = MaterialFactory(keyflow=self.kic)
        self.flow_a = IndicatorFlowFactory(origin_node_ids='1, 2, 3',
                                           destination_node_ids='4, 5',
                                           materials=[self.material1])
        self.flow_b = IndicatorFlowFactory(origin_node_ids='1, 2',
                                           destination_node_ids='3, 4, 5',
                                           materials=[self.material1])
        self.obj = FlowIndicatorFactory(flow_a=self.flow_a,
                                        flow_b=self.flow_b,
                                        keyflow=self.kic)
        self.post_data = dict(
            name = 'FlowIndicator',
            unit = 'Elmshorn',
            description = 'supernormal',
            indicator_type = 'A',
            flow_a = [self.flow_a],
            flow_b = [self.flow_b],
            keyflow = self.keyflow_id1,)
        self.put_data = self.post_data
        self.patch_data = self.post_data

    def test_post(self):
        pass

    def test_put_patch(self):
        pass

    def test_post_permission(self):
        pass

    def test_put_permission(self):
        pass

    def test_ComputeIndicator(self):
        ci = ComputeIndicator()
        ci.calculate_indicator_flow(self.flow_a)

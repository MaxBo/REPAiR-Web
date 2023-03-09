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
from repair.apps.statusquo.views.computation import ComputeIndicator


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
                           keyflow_pk=cls.kic_obj.id)
        cls.url_pk = dict(pk=cls.flowindicator_id)
        cls.post_data = dict(
            name = 'FlowIndicator',
            unit = 'Elmshorn',
            description = 'supernormal',
            indicator_type = 'A',
            flow_a = [cls.flow_a],
            flow_b = [cls.flow_b],
            keyflow = cls.keyflow_id1,)
        cls.put_data = cls.post_data
        cls.patch_data = cls.post_data

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.area1 = AreaFactory(id=cls.area_id1,
                                 )
        cls.area2 = AreaFactory(id=cls.area_id2,
                                     )
        cls.actor1 = ActorFactory(id=cls.actor_id1)
        cls.actor2 = ActorFactory(id=cls.actor_id2)
        cls.actor3 = ActorFactory(id=cls.actor_id3)
        cls.actor4 = ActorFactory(id=cls.actor_id4)
        cls.actor5 = ActorFactory(id=cls.actor_id5)
        cls.composition1 = CompositionFactory()
        cls.flow1 = Actor2ActorFactory(id=cls.flow_id1,
                                       keyflow=cls.kic_obj,
                                       composition=cls.composition1,
                                       origin=cls.actor1,
                                       destination=cls.actor2)
        cls.flow2 = Actor2ActorFactory(id=cls.flow_id2,
                                       keyflow=cls.kic_obj,
                                       composition=cls.composition1,
                                       origin=cls.actor2,
                                       destination=cls.actor3
                                       )
        cls.flow3 = Actor2ActorFactory(id=cls.flow_id3,
                                       keyflow=cls.kic_obj,
                                       composition=cls.composition1,
                                       origin=cls.actor3,
                                       destination=cls.actor5)
        cls.flow4 = Actor2ActorFactory(id=cls.flow_id4,
                                       keyflow=cls.kic_obj,
                                       composition=cls.composition1,
                                       origin=cls.actor5,
                                       destination=cls.actor4)
        cls.flow5 = Actor2ActorFactory(id=cls.flow_id5,
                                       keyflow=cls.kic_obj,
                                       composition=cls.composition1,
                                       origin=cls.actor5,
                                       destination=cls.actor3)
        cls.flow6 = Actor2ActorFactory(id=cls.flow_id6,
                                       keyflow=cls.kic_obj,
                                       composition=cls.composition1,
                                       origin=cls.actor1,
                                       destination=cls.actor3)
        cls.material1 = MaterialFactory(keyflow=cls.kic_obj)
        cls.flow_a = IndicatorFlowFactory(origin_node_ids='1, 2, 3',
                                          destination_node_ids='4, 5',
                                          materials=[cls.material1])
        cls.flow_b = IndicatorFlowFactory(origin_node_ids='1, 2',
                                          destination_node_ids='3, 4, 5',
                                          materials=[cls.material1])
        cls.obj = FlowIndicatorFactory(flow_a=cls.flow_a,
                                       flow_b=cls.flow_b,
                                       keyflow=cls.kic_obj)

    def test_post(self):
        pass

    def test_put_patch(self):
        pass

    def test_post_permission(self):
        pass

    def test_put_permission(self):
        pass

    def test_ComputeIndicator(self):
        ci = ComputeIndicator(self.keyflow_id1)
        ci.calculate_indicator_flow(self.flow_a)

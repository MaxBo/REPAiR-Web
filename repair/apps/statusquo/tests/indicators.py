# -*- coding: utf-8 -*-

from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status
from repair.tests.test import BasicModelPermissionTest, LoginTestCase

from repair.apps.statusquo.factories import (IndicatorFlow,
                                             FlowIndicator,
                                             )
from repair.apps.asmfa.factories import (AdministrativeLocationFactory,
                                         Actor2ActorFactory,
                                         ActorFactory,
                                         )
from repair.apps.studyarea.factories import (AreaFactory,
                                             )


class FlowIndicatorTest(BasicModelPermissionTest, APITestCase):

    casestudy = 17
    area1 = 1
    area2 = 2
    actor1 = 1
    actor2 = 2
    actor3 = 3
    actor4 = 4
    actor5 = 5
    flow1 = 1
    flow2 = 2
    flow3 = 3
    flow4 = 4
    flow5 = 5
    flow6 = 6
    flowindicator = 1

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "flowindicator"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.flowindicator)
        cls.post_data = dict(
            name = 'FlowIndicator',
            unit = 'Elmshorn',
            description = 'supernormal',
            indicator_type = 1,
            flow_a = self.indicatorflow_a,
            flow_b = self.indicatorflow_b,
            keyflow = self.keyflow_1,)
        cls.put_data = cls.post_data
        cls.patch_data = cls.post_data

    def setUp(self):
        super().setUp()
        self.area1 = AreaFactory(id=self.area1,
                                 )
        self.obj = AimFactory(casestudy=self.uic.casestudy,
                              id=self.aim)
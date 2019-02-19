# -*- coding: utf-8 -*-

from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status
from repair.tests.test import LoginTestCase, AdminAreaTest

from repair.apps.asmfa.factories import (ActivityFactory,
                                         ActivityGroupFactory,
                                         )


class ActivitygroupNaceCodeTest(LoginTestCase, APITestCase):

    casestudy = 17
    activitygroup = 90
    keyflow = 23

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "activitygroup"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflow)
        cls.url_pk = dict(pk=cls.activitygroup)

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

    def test_nace_codes(self):
        """
        Test if the Nace-Codes of the activities of an activitygroup
        are calculated correctly
        """

        self.assertSetEqual(set(self.activitygroup1.nace_codes),
                            {'NACE1', 'NACE2'})
        self.assertSetEqual(set(self.activitygroup2.nace_codes), {'NACE3'})

    def test_nace_code_serializer(self):
        """
        Test if the Serializer returns the Nace-Codes
        of the activities of an activitygroup
        """
        url = self.url_key + '-detail'
        kwargs={**self.url_pks, 'pk': self.activitygroup1.pk,}
        response = self.get_check_200(url, **kwargs)
        self.assertSetEqual(set(response.data['nace']),
                            {'NACE1', 'NACE2'})

        kwargs={**self.url_pks, 'pk': self.activitygroup2.pk,}
        response = self.get_check_200(url, **kwargs)
        self.assertSetEqual(set(response.data['nace']), {'NACE3'})

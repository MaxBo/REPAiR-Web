# -*- coding: utf-8 -*-

from django.urls import reverse
from rest_framework import status
from test_plus import APITestCase
from repair.tests.test import BasicModelTest

from repair.apps.asmfa.factories import (KeyflowFactory,
                                         KeyflowInCasestudyFactory)


class KeyflowTest(BasicModelTest, APITestCase):
    casestudy = 17
    keyflow = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cs_url = cls.baseurl + reverse('casestudy-detail',
                                           kwargs=dict(pk=cls.casestudy))
        cls.keyflow_url = cls.baseurl + reverse('keyflow-detail',
                                                 kwargs=dict(pk=cls.keyflow))
        cls.url_key = "keyflow"
        cls.url_pks = dict()
        cls.url_pk = dict(pk=1)
        cls.post_data = dict(name='posttestname',
                             casestudies=[cls.cs_url], code='Food')
        cls.put_data = dict(name='puttestname',
                            casestudies=[cls.cs_url],
                            code='Food')
        cls.patch_data = dict(name='patchtestname')

    def setUp(self):
        super().setUp()
        self.obj = KeyflowFactory()


class KeyflowInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    keyflow = 3
    sub_urls = [
    "activitygroups",
    "activities",
    "actors",
    "administrative_locations",
    "operational_locations",
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cs_url = cls.baseurl + reverse('casestudy-detail',
                                   kwargs=dict(pk=cls.casestudy))
        cls.keyflow_url = cls.baseurl + reverse('keyflow-detail',
                                                 kwargs=dict(pk=cls.keyflow))


        cls.url_key = "keyflowincasestudy"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.keyflow)

        cls.put_data = dict(note='new_put_note',
                             keyflow=cls.keyflow_url,
                             )
        cls.post_data = dict(note='new_note',
                             keyflow=cls.keyflow_url,
                             )

        cls.patch_data = dict(note='patchtestnote')

    def setUp(self):
        super().setUp()
        self.obj = KeyflowInCasestudyFactory(casestudy=self.uic.casestudy,
                                              keyflow__id=self.keyflow)

    def test_post(self):
        url = reverse(self.url_key +'-list', kwargs=self.url_pks)
        # post
        response = self.client.post(url, self.post_data)
        for key in self.post_data:
            assert response.data[key] == self.post_data[key]
        assert response.status_code == status.HTTP_201_CREATED

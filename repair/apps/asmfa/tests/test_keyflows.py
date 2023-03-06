# -*- coding: utf-8 -*-

from django.urls import reverse
import unittest
from rest_framework import status
from test_plus import APITestCase
from repair.tests.test import BasicModelPermissionTest

from repair.apps.asmfa.factories import (KeyflowFactory,
                                         KeyflowInCasestudyFactory,
                                         ProductFactory,
                                         WasteFactory)


class KeyflowTest(BasicModelPermissionTest, APITestCase):
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

    @classmethod
    def setUpTestData(self):
        super().setUpTestData()
        self.obj = KeyflowFactory()


class KeyflowInCaseStudyTest(BasicModelPermissionTest, APITestCase):

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
                            keyflow=cls.keyflow,
                            )
        cls.post_data = dict(note='new_note',
                             keyflow=cls.keyflow,
                             )

        cls.patch_data = dict(note='patchtestnote')
        cls.obj = cls.kic_obj

    def test_post(self):
        url = reverse(self.url_key + '-list', kwargs=self.url_pks)
        # post
        response = self.client.post(url, self.post_data)
        for key in self.post_data:
            assert response.data[key] == self.post_data[key]
        assert response.status_code == status.HTTP_201_CREATED


class ProductTest(BasicModelPermissionTest, APITestCase):
    keyflowincasestudy = 5
    keyflow = 7
    casestudy = 4
    product = 2

    @classmethod
    def setUpTestData(self):
        super().setUpTestData()
        self.obj = ProductFactory(id=self.product)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "product"
        cls.url_pks = dict()
        cls.url_pk = dict(pk=cls.product)
        cls.put_data = dict(name='testname',
                            nace='testnace',
                            cpa='testcpa',
                            fractions=[]
                            )
        cls.post_data = cls.put_data
        cls.patch_data = cls.put_data


class WasteTest(BasicModelPermissionTest, APITestCase):
    keyflowincasestudy = 5
    keyflow = 7
    casestudy = 4
    waste = 2

    @classmethod
    def setUpTestData(self):
        super().setUpTestData()
        self.obj = WasteFactory(id=self.waste)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "waste"
        cls.url_pks = dict()
        cls.url_pk = dict(pk=cls.waste)
        cls.put_data = dict(name='testname',
                            nace='testnace',
                            ewc ='testewc',
                            wastetype ='testtype',
                            hazardous = False,
                            fractions=[]
                            )
        cls.post_data = cls.put_data
        cls.patch_data = cls.put_data

# -*- coding: utf-8 -*-

from test_plus import APITestCase
from repair.tests.test import BasicModelTest

from repair.apps.asmfa.factories import (KeyflowInCasestudyFactory,
                                         Group2GroupFactory,
                                         Activity2ActivityFactory,
                                         Actor2ActorFactory)


class Activity2ActivityInMaterialInCaseStudyTest(BasicModelTest, APITestCase):
    """
    MAX:
    1. origin/destination can be in other casestudies than activity2activity
    2. set amount default in model to 0
    """
    casestudy = 17
    keyflow = 3
    origin = 20
    destination = 12
    product = 16
    activity2activity = 13
    keyflowincasestudy = 45
    activitygroup = 76

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "activity2activity"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.activity2activity)

        cls.put_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            product=cls.product,
                            )
        cls.post_data = dict(origin=cls.origin,
                             destination=cls.destination,
                             product=cls.product,
                             )
        cls.patch_data = dict(origin=cls.origin,
                              destination=cls.destination,
                              product=cls.product,
                              )
        cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.obj = Activity2ActivityFactory(
            id=self.activity2activity,
            origin__id=self.origin,
            origin__activitygroup__keyflow=kic_obj,
            destination__id=self.destination,
            destination__activitygroup__keyflow=kic_obj,
            product__id=self.product,
            product__keyflow=kic_obj,
            keyflow=kic_obj
            )


class Actor2AtcorInMaterialInCaseStudyTest(BasicModelTest, APITestCase):
    casestudy = 17
    keyflow = 3
    origin = 20
    destination = 12
    product = 16
    actor2actor = 13
    keyflowincasestudy = 45
    activitygroup = 76

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "actor2actor"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.actor2actor)

        cls.put_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            product=cls.product,
                            )
        cls.post_data = dict(origin=cls.origin,
                             destination=cls.destination,
                             product=cls.product,
                             )
        cls.patch_data = dict(origin=cls.origin,
                              destination=cls.destination,
                              product=cls.product,
                              )
        cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.obj = Actor2ActorFactory(id=self.actor2actor,
                                      origin__id=self.origin,
                                      origin__activity__activitygroup__keyflow=kic_obj,
                                      destination__id=self.destination,
                                      destination__activity__activitygroup__keyflow=kic_obj,
                                      product__id=self.product,
                                      product__keyflow=kic_obj,
                                      keyflow=kic_obj,
                                      )


class Group2GroupInKeyflowInCaseStudyTest(BasicModelTest, APITestCase):
    casestudy = 17
    keyflow = 3
    origin = 20
    destination = 12
    product = 16
    group2group = 13
    keyflowincasestudy = 45
    activitygroup = 76

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "group2group"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.group2group)

        cls.put_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            product=cls.product,
                            )
        cls.post_data = dict(origin=cls.origin,
                             destination=cls.destination,
                             product=cls.product,
                             )
        cls.patch_data = dict(origin=cls.origin,
                              destination=cls.destination,
                              product=cls.product,
                              )
        cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.obj = Group2GroupFactory(id=self.group2group,
                                      origin__id=self.origin,
                                      origin__keyflow=kic_obj,
                                      destination__id=self.destination,
                                      destination__keyflow=kic_obj,
                                      product__id=self.product,
                                      product__keyflow=kic_obj,
                                      keyflow=kic_obj,
                                      )

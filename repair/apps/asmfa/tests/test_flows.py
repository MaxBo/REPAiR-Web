# -*- coding: utf-8 -*-

from test_plus import APITestCase
from repair.tests.test import BasicModelPermissionTest

from repair.apps.asmfa.factories import (KeyflowInCasestudyFactory,
                                         Group2GroupFactory,
                                         Activity2ActivityFactory,
                                         Actor2ActorFactory,
                                         CompositionFactory,
                                         MaterialFactory)


class Activity2ActivityInMaterialInCaseStudyTest(BasicModelPermissionTest, APITestCase):
    """
    MAX:
    1. origin/destination can be in other casestudies than activity2activity
    2. set amount default in model to 0
    """
    casestudy = 17
    keyflow = 3
    origin = 20
    destination = 12
    composition = 16
    activity2activity = 13
    keyflowincasestudy = 45
    activitygroup = 76
    material_1 = 10
    material_2 = 11
    comp_data = {'name': 'testname', 'nace': 'testnace',
                 "fractions": [{ "material": material_1,
                                 "fraction": 0.4},
                               { "material": material_2,
                                 "fraction": 0.6}]}
    do_not_check = ['composition']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "activity2activity"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.activity2activity)
        cls.put_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            composition=cls.comp_data,
                            )
        cls.post_data = dict(origin=cls.origin,
                             destination=cls.destination,
                             composition=cls.comp_data,
                             format='json'
                             )
        cls.patch_data = dict(origin=cls.origin,
                              destination=cls.destination,
                              composition=cls.comp_data,
                              )
        cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.mat_obj_1 = MaterialFactory(id=self.material_1,
                                        keyflow=kic_obj)
        self.mat_obj_2 = MaterialFactory(id=self.material_2,
                                         keyflow=kic_obj)
        self.obj = Activity2ActivityFactory(
            id=self.activity2activity,
            origin__id=self.origin,
            origin__activitygroup__keyflow=kic_obj,
            destination__id=self.destination,
            destination__activitygroup__keyflow=kic_obj,
            keyflow=kic_obj,
            )


class Actor2AtcorInMaterialInCaseStudyTest(BasicModelPermissionTest, APITestCase):
    casestudy = 17
    keyflow = 3
    origin = 20
    destination = 12
    product = 16
    actor2actor = 13
    keyflowincasestudy = 45
    activitygroup = 76
    material_1 = 10
    material_2 = 11
    comp_data = {'name': 'testname', 'nace': 'testnace',
                 "fractions": [{ "material": material_1,
                                 "fraction": 0.4},
                               { "material": material_2,
                                 "fraction": 0.6}]}
    do_not_check = ['composition']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "actor2actor"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.actor2actor)

        cls.put_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            composition=cls.comp_data,
                            )
        cls.post_data = dict(origin=cls.origin,
                             destination=cls.destination,
                             composition=cls.comp_data,
                             )
        cls.patch_data = dict(origin=cls.origin,
                              destination=cls.destination,
                              composition=cls.comp_data,
                              )
        cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.mat_obj_1 = MaterialFactory(id=self.material_1,
                                             keyflow=kic_obj)
        self.mat_obj_2 = MaterialFactory(id=self.material_2,
                                             keyflow=kic_obj)
        self.obj = Actor2ActorFactory(id=self.actor2actor,
                                      origin__id=self.origin,
                                      origin__activity__activitygroup__keyflow=kic_obj,
                                      destination__id=self.destination,
                                      destination__activity__activitygroup__keyflow=kic_obj,
                                      keyflow=kic_obj,
                                      )


class Group2GroupInKeyflowInCaseStudyTest(BasicModelPermissionTest, APITestCase):
    casestudy = 17
    keyflow = 3
    origin = 20
    destination = 12
    product = 16
    group2group = 13
    keyflowincasestudy = 45
    activitygroup = 76
    material_1 = 10
    material_2 = 11
    comp_data = {'name': 'testname', 'nace': 'testnace',
                 "fractions": [{ "material": material_1,
                                 "fraction": 0.4},
                               { "material": material_2,
                                 "fraction": 0.6}]}
    do_not_check = ['composition']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "group2group"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.group2group)

        cls.put_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            composition=cls.comp_data,
                            )
        cls.post_data = dict(origin=cls.origin,
                             destination=cls.destination,
                             composition=cls.comp_data,
                             )
        cls.patch_data = dict(origin=cls.origin,
                              destination=cls.destination,
                              composition=cls.comp_data,
                              )
        cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.mat_obj_1 = MaterialFactory(id=self.material_1,
                                             keyflow=kic_obj)
        self.mat_obj_2 = MaterialFactory(id=self.material_2,
                                             keyflow=kic_obj)
        self.obj = Group2GroupFactory(id=self.group2group,
                                      origin__id=self.origin,
                                      origin__keyflow=kic_obj,
                                      destination__id=self.destination,
                                      destination__keyflow=kic_obj,
                                      keyflow=kic_obj,
                                      )

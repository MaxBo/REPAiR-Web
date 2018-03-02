# -*- coding: utf-8 -*-

from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status
from repair.tests.test import BasicModelPermissionTest, LoginTestCase

from repair.apps.statusquo.factories import (SustainabilityFieldFactory,
                                             TargetValueFactory,
                                             TargetSpatialReferenceFactory,
                                             AreaOfProtectionFactory,
                                             ImpactCategoryFactory,
                                             TargetFactory)

class SustainabilityFieldTest(BasicModelPermissionTest, APITestCase):

    sustainability = 20

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "sustainabilityfield"
        cls.url_pks = dict()
        cls.url_pk = dict(pk=cls.sustainability)
        cls.post_data = dict(name="name sustainability")
        cls.put_data = cls.post_data
        cls.patch_data = cls.post_data

    def setUp(self):
        super().setUp()
        self.obj = SustainabilityFieldFactory(id=self.sustainability)


class TargetValueTest(BasicModelPermissionTest, APITestCase):

    targetvalue = 20

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "targetvalue"
        cls.url_pks = dict()
        cls.url_pk = dict(pk=cls.targetvalue)
        cls.post_data = dict(text="name targetvalue",
                             number=21.0,
                             factor=31.0)
        cls.put_data = cls.post_data
        cls.patch_data = cls.post_data

    def setUp(self):
        super().setUp()
        self.obj = TargetValueFactory(id=self.targetvalue)


class TargetSpatialReferenceTest(BasicModelPermissionTest, APITestCase):

    targetspatialreference = 20

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "targetspatialreference"
        cls.url_pks = dict()
        cls.url_pk = dict(pk=cls.targetspatialreference)
        cls.post_data = dict(text="text targetspatialreference",
                             name="name targetspatialreference")
        cls.put_data = cls.post_data
        cls.patch_data = cls.post_data

    def setUp(self):
        super().setUp()
        self.obj = TargetSpatialReferenceFactory(
            id=self.targetspatialreference)


class AreaOfProtectionTest(BasicModelPermissionTest, APITestCase):

    areaofprotection = 20
    sustainabilityfield = 31

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "areaofprotection"
        cls.url_pks = dict(sustainability_pk = cls.sustainabilityfield)
        cls.url_pk = dict(pk=cls.areaofprotection)
        cls.post_data = dict(sustainability_field=cls.sustainabilityfield,
                             name="name areaofprotection")
        cls.put_data = cls.post_data
        cls.patch_data = cls.post_data

    def setUp(self):
        super().setUp()
        self.obj = AreaOfProtectionFactory(id=self.areaofprotection,
                                           sustainability_field__id=
                                           self.sustainabilityfield)


class ImpactCategoryTest(BasicModelPermissionTest, APITestCase):

    impactcategory = 43
    areaofprotection = 20
    sustainabilityfield = 53

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "impactcategory"
        cls.url_pks = dict(sustainability_pk = cls.sustainabilityfield)
        cls.url_pk = dict(pk=cls.impactcategory)
        cls.post_data = dict(area_of_protection=cls.areaofprotection,
                             name="name impact category",
                             spatial_differentiation=True)
        cls.put_data = cls.post_data
        cls.patch_data = cls.post_data

    def setUp(self):
        super().setUp()
        self.obj = ImpactCategoryFactory(
            id=self.impactcategory,
            area_of_protection__id=self.areaofprotection,
            area_of_protection__sustainability_field__id=
            self.sustainabilityfield)


class TargetTest(BasicModelPermissionTest, APITestCase):

    target = 12
    userincasestudy = 23
    aim = 34
    impact_category = 45
    target_value = 56
    spatial_reference = 67
    casestudy = 17
    user = 18
    do_not_check = ['user']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_url = reverse('userincasestudy-detail',
                           kwargs=dict(pk=cls.userincasestudy,
                                       casestudy_pk=cls.casestudy))
        cls.url_key = "target"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           user_pk=cls.userincasestudy)
        cls.url_pk = dict(pk=cls.target)
        cls.post_data = dict(aim=cls.aim,
                             impact_category=cls.impact_category,
                             target_value=cls.target_value,
                             spatial_reference=cls.spatial_reference,
                             user=user_url)
        cls.put_data = cls.post_data
        cls.patch_data = cls.post_data

    def setUp(self):
        super().setUp()
        self.obj = TargetFactory(id=self.target,
                                 user=self.uic,
                                 aim__id=self.aim,
                                 impact_category__id=self.impact_category,
                                 target_value__id=self.target_value,
                                 spatial_reference__id=self.spatial_reference,
                                 )
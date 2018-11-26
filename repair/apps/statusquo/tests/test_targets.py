# -*- coding: utf-8 -*-

from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status
from repair.tests.test import BasicModelPermissionTest, LoginTestCase

from repair.apps.statusquo.factories import (SustainabilityFieldFactory,
                                             TargetValueFactory,
                                             TargetSpatialReferenceFactory,
                                             AreaOfProtectionFactory,
                                             ImpactCategoryFactory)


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


class ImpactCategoriesAndAreasOfProtectionTest(LoginTestCase, APITestCase):
    """
    Test if the api finds the right impact categories for a susatainability
    field via the area of protection.
    Areas 1 and 2 should reference to sustainability field 1 and the other area
    is assigned to sustainability field 2. Impact categories 1 and 2 are
    assigned to area 1. Impact categories 3 and 4 are assigned to the areas 2
    and 3.
    Check now if sustainability field 1 has 3 impact categories and
    sustainability field 2 has 1 impact category.
    """
    baseurl = 'http://testserver'
    ic_1 = 1
    ic_2 = 2
    ic_3 = 3
    ic_4 = 4
    aop_1 = 1
    aop_2 = 2
    aop_3 = 3
    sf_1 = 1
    sf_2 = 2

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "impactcategory"
        cls.url_pks_1 = dict(sustainability_pk=cls.sf_1)
        cls.url_pks_2 = dict(sustainability_pk=cls.sf_2)
        #cls.url_pk = dict(pk=cls.impactcategory)


    def setUp(self):
        super().setUp()
        self.sf_obj_1 = SustainabilityFieldFactory(id=self.sf_1)
        self.sf_obj_2 = SustainabilityFieldFactory(id=self.sf_2)
        self.aop_obj_1 = AreaOfProtectionFactory(id=self.aop_1,
                                                 sustainability_field=
                                                 self.sf_obj_1)
        self.aop_obj_2 = AreaOfProtectionFactory(id=self.aop_2,
                                                 sustainability_field=
                                                 self.sf_obj_1)
        self.aop_obj_3 = AreaOfProtectionFactory(id=self.aop_3,
                                                 sustainability_field=
                                                 self.sf_obj_2)
        self.ic_obj_1 = ImpactCategoryFactory(id=self.ic_1,
                                              area_of_protection=
                                              self.aop_obj_1)
        self.ic_obj_2 = ImpactCategoryFactory(id=self.ic_2,
                                              area_of_protection=
                                              self.aop_obj_1)
        self.ic_obj_3 = ImpactCategoryFactory(id=self.ic_3,
                                              area_of_protection=
                                              self.aop_obj_2)
        self.ic_obj_4 = ImpactCategoryFactory(id=self.ic_4,
                                              area_of_protection=
                                              self.aop_obj_3)

    def test_list(self):
        response = self.get_check_200(self.url_key + '-list', **self.url_pks_1)
        assert len(response.data) == 3
        response = self.get_check_200(self.url_key + '-list', **self.url_pks_2)
        assert len(response.data) == 1

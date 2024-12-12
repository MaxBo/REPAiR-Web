# -*- coding: utf-8 -*-

from test_plus import APITestCase
from repair.tests.test import BasicModelPermissionTest

from repair.apps.asmfa.factories import (KeyflowInCasestudyFactory,
                                         ProductFactory)


class ProductsTest(BasicModelPermissionTest, APITestCase):
    casestudy = 17
    keyflow = 3
    product = 16
    keyflowincasestudy = 45

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "product"
        cls.url_pks = dict()
        cls.url_pk = dict(pk=cls.product)
        cls.put_data = dict(cpa="test", fractions=[])
        cls.post_data = cls.put_data
        cls.patch_data = dict(name="other name")

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.obj = ProductFactory(id=cls.product)

# -*- coding: utf-8 -*-

from test_plus import APITestCase
from repair.tests.test import BasicModelPermissionTest

from repair.apps.asmfa.factories import (KeyflowInCasestudyFactory,
                                         ProductFactory)


class ProductsInKeyflowInCasestudyTest(BasicModelPermissionTest, APITestCase):
    """
    MAX:
        1. Products is not in casestudy/xx/keyflows/xx/
        2. not shure what fractions is
    """
    casestudy = 17
    keyflow = 3
    product = 16
    keyflowincasestudy = 45

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "product"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.product)
        cls.put_data = dict(fractions=[])
        cls.post_data = cls.put_data
        cls.patch_data = dict(name="other name")
        cls.sub_urls = ['keyflow']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.obj = ProductFactory(id=self.product,
                                  keyflow=kic_obj,
                                  )

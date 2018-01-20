# -*- coding: utf-8 -*-

from test_plus import APITestCase
from repair.tests.test import BasicModelTest

from repair.apps.asmfa.factories import (KeyflowInCasestudyFactory,
                                         GroupStockFactory,
                                         ActivityStockFactory,
                                         ActorStockFactory)


class ActivitystockInKeyflowInCasestudyTest(BasicModelTest, APITestCase):
    """
    MAX:
    1. set stock.amount default value to 0
    2. post test not working:
        product should not be required (api/docs)
        also not working via the api html post"""
    casestudy = 17
    keyflow = 3
    origin = 20
    product = 16
    activitystock = 13
    keyflowincasestudy = 45
    activitygroup = 76
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "activitystock"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.activitystock)
        cls.put_data = dict(origin=cls.origin,
                            product=cls.product,
                             )
        cls.post_data = dict(origin=cls.origin,
                             product=cls.product,
                             )
        cls.patch_data = dict(origin=cls.origin,
                              product=cls.product,
                             )
        #cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.obj = ActivityStockFactory(id=self.activitystock,
                                        origin__id=self.origin,
                                        origin__activitygroup__id=self.activitygroup,
                                        origin__activitygroup__keyflow=kic_obj,
                                        product__id=self.product,
                                        product__keyflow=kic_obj,
                                        keyflow=kic_obj,
                                        )


class ActorstockInKeyflowInCasestudyTest(BasicModelTest, APITestCase):
    """
    MAX:
    1. set stock.amount default value to 0
    2. post test not working:
        product should not be required (api/docs)
        also not working via the api html post"""
    casestudy = 17
    keyflow = 3
    origin = 20
    product = 16
    actorstock = 13
    keyflowincasestudy = 45
    activitygroup = 76
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "actorstock"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.actorstock)
        cls.put_data = dict(origin=cls.origin,
                            product=cls.product,
                             )
        cls.post_data = dict(origin=cls.origin,
                             product=cls.product,
                             )
        cls.patch_data = dict(origin=cls.origin,
                              product=cls.product,
                             )
        #cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.obj = ActorStockFactory(id=self.actorstock,
                                     origin__id=self.origin,
                                     origin__activity__activitygroup__id=self.activitygroup,
                                     origin__activity__activitygroup__keyflow=kic_obj,
                                     product__id=self.product,
                                     product__keyflow=kic_obj,
                                     keyflow=kic_obj,
                                     )


class GroupstockInKeyflowInCasestudyTest(BasicModelTest, APITestCase):
    """
    MAX:
    1. set stock.amount default value to 0
    2. post test not working:
        product should not be required (api/docs)
        also not working via the api html post"""
    casestudy = 17
    keyflow = 3
    origin = 20
    product = 16
    groupstock = 13
    keyflowincasestudy = 45
    activitygroup = 76
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "groupstock"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.groupstock)
        cls.put_data = dict(origin=cls.origin,
                            product=cls.product,
                             )
        cls.post_data = dict(origin=cls.origin,
                             product=cls.product,
                             )
        cls.patch_data = dict(origin=cls.origin,
                              product=cls.product,
                             )
        #cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.obj = GroupStockFactory(id=self.groupstock,
                                     origin__id=self.origin,
                                     origin__keyflow=kic_obj,
                                     product__id=self.product,
                                     product__keyflow=kic_obj,
                                     keyflow=kic_obj,
                                     )

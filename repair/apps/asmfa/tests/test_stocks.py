# -*- coding: utf-8 -*-

from test_plus import APITestCase
from repair.tests.test import BasicModelPermissionTest

from repair.apps.asmfa.factories import (KeyflowInCasestudyFactory,
                                         GroupStockFactory,
                                         ActivityStockFactory,
                                         ActorStockFactory,
                                         MaterialFactory)
import json


class ActivitystockInKeyflowInCasestudyTest(BasicModelPermissionTest, APITestCase):
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
        cls.url_key = "activitystock"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.activitystock)
        cls.put_data = dict(origin=cls.origin,
                            composition=cls.comp_data,
                            )
        cls.post_data = dict(origin=cls.origin,
                             composition=cls.comp_data,
                             )
        cls.patch_data = dict(origin=cls.origin,
                              composition=cls.comp_data,
                              )
        #cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.mat_obj_1 = MaterialFactory(id=self.material_1,
                                             keyflow=kic_obj)
        self.mat_obj_2 = MaterialFactory(id=self.material_2,
                                             keyflow=kic_obj)
        self.obj = ActivityStockFactory(id=self.activitystock,
                                        origin__id=self.origin,
                                        origin__activitygroup__id=self.activitygroup,
                                        origin__activitygroup__keyflow=kic_obj,
                                        keyflow=kic_obj,
                                        )


class ActorstockInKeyflowInCasestudyTest(BasicModelPermissionTest, APITestCase):
    """"""
    casestudy = 17
    keyflow = 3
    origin = 20
    product = 16
    actorstock = 13
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
        cls.url_key = "actorstock"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.actorstock)
        cls.put_data = dict(origin=cls.origin,
                            composition=cls.comp_data,
                            )
        cls.post_data = dict(origin=cls.origin,
                             composition=cls.comp_data,
                             )
        cls.patch_data = dict(origin=cls.origin,
                              composition=cls.comp_data,
                              )
        #cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.mat_obj_1 = MaterialFactory(id=self.material_1,
                                             keyflow=kic_obj)
        self.mat_obj_2 = MaterialFactory(id=self.material_2,
                                             keyflow=kic_obj)
        self.obj = ActorStockFactory(
            id=self.actorstock,
            origin__id=self.origin,
            origin__activity__activitygroup__id=self.activitygroup,
            origin__activity__activitygroup__keyflow=kic_obj,
            keyflow=kic_obj,
            )

    def test_post_get(self):
        """
        Test if user can post without permission
        """
        filterdata = json.dumps([
            {'function': 'origin__activity__activitygroup__id__in',
             'values': [1, 2],}])
        post_data1 = dict(aggregation_level='activitygroup',
                             material=json.dumps(dict(aggregate=True,
                                                      id=self.material_1)),
                             filters=filterdata)
        post_data2 = dict(aggregation_level='activitygroup',
                          material=json.dumps(dict(aggregate=False,
                                                   id=self.material_1)),
                          filters=filterdata)
        post_data3 = dict(aggregation_level='activitygroup',
                          material=json.dumps(dict(aggregate=False,
                                                   id=self.material_1)),
                          filters=filterdata,
                          spatial_level=json.dumps(dict(activity=dict(id=1,
                                                                      level=1))))
        url = '/api/casestudies/{}/keyflows/{}/actorstock/?GET=true'.format(self.casestudy, self.keyflow)
        for post_data in [post_data1, post_data2, post_data3]:
            response = self.post(
                url,
                data=post_data,
                extra={'format': 'json'})
            self.response_200()


class GroupstockInKeyflowInCasestudyTest(BasicModelPermissionTest, APITestCase):
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
        cls.url_key = "groupstock"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.groupstock)
        cls.put_data = dict(origin=cls.origin,
                            composition=cls.comp_data,
                            )
        cls.post_data = dict(origin=cls.origin,
                             composition=cls.comp_data,
                             )
        cls.patch_data = dict(origin=cls.origin,
                              composition=cls.comp_data,
                              )
        #cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.mat_obj_1 = MaterialFactory(id=self.material_1,
                                             keyflow=kic_obj)
        self.mat_obj_2 = MaterialFactory(id=self.material_2,
                                             keyflow=kic_obj)
        self.obj = GroupStockFactory(id=self.groupstock,
                                     origin__id=self.origin,
                                     origin__keyflow=kic_obj,
                                     keyflow=kic_obj,
                                     )

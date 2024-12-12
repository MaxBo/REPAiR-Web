# -*- coding: utf-8 -*-

from test_plus import APITestCase
from repair.tests.test import BasicModelPermissionTest

from repair.apps.asmfa.factories import (KeyflowInCasestudyFactory,
                                         GroupStockFactory,
                                         ActivityStockFactory,
                                         ActorStockFactory,
                                         MaterialFactory,
                                         CompositionFactory,
                                         ActivityGroupFactory,
                                         ActivityFactory,
                                         Actor2ActorFactory,
                                         ActorFactory,
                                         )
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
                           keyflow_pk=cls.keyflow)
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

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mat_obj_1 = MaterialFactory(id=cls.material_1,
                                        keyflow=cls.kic_obj)
        cls.mat_obj_2 = MaterialFactory(id=cls.material_2,
                                        keyflow=cls.kic_obj)
        cls.obj = ActivityStockFactory(id=cls.activitystock,
                                       origin__id=cls.origin,
                                       origin__activitygroup__id=cls.activitygroup,
                                       origin__activitygroup__keyflow=cls.kic_obj,
                                       keyflow=cls.kic_obj,
                                       )


class ActorstockInKeyflowInCasestudyTest(BasicModelPermissionTest, APITestCase):
    """"""
    casestudy = 17
    keyflow = 3
    origin = 20
    destination = 12
    product = 16
    actor2actor1 = 13
    actor2actor2 = 14
    keyflowincasestudy = 45
    activitygroup = 76
    material_1 = 10
    material_2 = 11
    actor1id = 12
    actor2id = 20
    actorstock = 56
    actorstock2 = 58
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
                           keyflow_pk=cls.keyflow)
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

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mat_obj_1 = MaterialFactory(id=cls.material_1,
                                         keyflow=cls.kic_obj)
        cls.mat_obj_2 = MaterialFactory(id=cls.material_2,
                                         keyflow=cls.kic_obj)
        cls.comp1 = CompositionFactory(name='composition1',
                                        nace='nace1')
        cls.comp2 = CompositionFactory(name='composition2',
                                        nace='nace2')
        cls.activitygroup1 = ActivityGroupFactory(keyflow=cls.kic_obj)
        cls.activity1 = ActivityFactory(activitygroup=cls.activitygroup1)
        cls.actor1 = ActorFactory(id=cls.actor1id, activity=cls.activity1)
        cls.activitygroup2 = ActivityGroupFactory(keyflow=cls.kic_obj)
        cls.activity2 = ActivityFactory(activitygroup=cls.activitygroup2)
        cls.actor2 = ActorFactory(id=cls.actor2id, activity=cls.activity2)
        cls.actor3 = ActorFactory(activity=cls.activity2)
        cls.act2act1 = Actor2ActorFactory(id=cls.actor2actor1,
                                           origin=cls.actor1,
                                           destination=cls.actor2,
                                           keyflow=cls.kic_obj,
                                           composition=cls.comp1,
                                           )
        cls.act2act2 = Actor2ActorFactory(id=cls.actor2actor2,
                                           origin=cls.actor2,
                                           destination=cls.actor3,
                                           keyflow=cls.kic_obj,
                                           composition=cls.comp2,
                                           )
        cls.actorstock1 = ActorStockFactory(id=cls.actorstock,
                                             keyflow=cls.kic_obj,
                                             origin=cls.actor1)
        cls.actorstock2 = ActorStockFactory(id=cls.actorstock2,
                                             keyflow=cls.kic_obj,
                                             origin=cls.actor2)
        cls.obj = cls.actorstock1

    def test_post_get(self):
        """
        Test if user can post without permission
        """
        filterdata = json.dumps([{
            'link': 'or',
            'functions': [
                {
                    'function': 'origin__activity__activitygroup__id__in',
                    'values': [1, 2],
                }
            ]
        }])
        post_data1 = dict(aggregation_level='activitygroup',
                             materials=json.dumps(dict(aggregate=True,
                                                       ids=[self.material_1])),
                             filters=filterdata)
        post_data2 = dict(aggregation_level='activitygroup',
                          materials=json.dumps(dict(aggregate=False,
                                                    ids=[self.material_1])),
                          filters=filterdata)
        post_data3 = dict(aggregation_level='activitygroup',
                          materials=json.dumps(dict(aggregate=False,
                                                    ids=[self.material_1])),
                          filters=filterdata,
                          spatial_level=json.dumps(dict(activity=dict(id=1,
                                                                    level=1))))
        url = '/api/casestudies/{}/keyflows/{}/actorstock/?GET=true'.format(
            self.casestudy, self.keyflow)
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
                           keyflow_pk=cls.keyflow)
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

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.mat_obj_1 = MaterialFactory(id=cls.material_1,
                                        keyflow=cls.kic_obj)
        cls.mat_obj_2 = MaterialFactory(id=cls.material_2,
                                        keyflow=cls.kic_obj)
        cls.obj = GroupStockFactory(id=cls.groupstock,
                                    origin__id=cls.origin,
                                    origin__keyflow=cls.kic_obj,
                                    keyflow=cls.kic_obj,
                                    )

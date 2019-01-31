# -*- coding: utf-8 -*-

from test_plus import APITestCase
from repair.tests.test import BasicModelPermissionTest
from repair.apps.asmfa.views.flows import filter_by_material
from repair.apps.asmfa.models.keyflows import Material
from repair.apps.asmfa.models.flows import Actor2Actor, FractionFlow
from repair.apps.asmfa.factories import (KeyflowInCasestudyFactory,
                                         Group2GroupFactory,
                                         Activity2ActivityFactory,
                                         Actor2ActorFactory,
                                         CompositionFactory,
                                         MaterialFactory,
                                         ProductFractionFactory,
                                         ActorFactory,
                                         ActivityFactory,
                                         ActivityGroupFactory,
                                         ProductFractionFactory,
                                         PublicationInCasestudyFactory,
                                         ProcessFactory
                                         )
import json


class Activity2ActivityInMaterialInCaseStudyTest(BasicModelPermissionTest,
                                                 APITestCase):
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
                            process=None
                            )
        cls.post_data = dict(origin=cls.origin,
                             destination=cls.destination,
                             composition=cls.comp_data,
                             process=None,
                             format='json'
                             )
        cls.patch_data = dict(origin=cls.origin,
                              destination=cls.destination,
                              composition=cls.comp_data,
                              process=None
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


class Actor2ActorInMaterialInCaseStudyTest(BasicModelPermissionTest,
                                           APITestCase):
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
    material_3 = 12
    actor1id = 12
    actor2id = 20
    comp_data1 = {'name': 'testname', 'nace': 'testnace',
                 "fractions": [{ "material": material_1,
                                 "fraction": 0.4},
                               { "material": material_2,
                                 "fraction": 0.6}]}
    comp_data2 = {'name': 'testname2', 'nace': 'testnace2',
                  "fractions": [{ "material": material_1,
                                 "fraction": 0.5},
                               { "material": material_2,
                                 "fraction": 0.5}]}
    do_not_check = ['composition']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "actor2actor"

        cls.process = ProcessFactory(name='test-process')
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.actor2actor1)

        cls.put_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            composition=cls.comp_data1,
                            process=None
                            )
        cls.post_data = dict(origin=cls.origin,
                             destination=cls.destination,
                             composition=cls.comp_data1,
                             process=None,
                             amount=100
                             )
        cls.patch_data = dict(origin=cls.origin,
                              destination=cls.destination,
                              composition=cls.comp_data1,
                              process=cls.process.id,
                              amount=50
                              )
        #cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        self.kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                                 casestudy=self.uic.casestudy,
                                                 keyflow__id=self.keyflow)
        self.mat_obj_1 = MaterialFactory(id=self.material_1,
                                         keyflow=self.kic_obj,
                                         parent=None)
        self.mat_obj_2 = MaterialFactory(id=self.material_2,
                                         keyflow=self.kic_obj,
                                         parent=self.mat_obj_1)
        self.mat_obj_3 = MaterialFactory(id=self.material_3,
                                         keyflow=self.kic_obj,
                                         parent=self.mat_obj_2)
        self.comp1 = CompositionFactory(name='composition1',
                                        nace='nace1')
        self.comp2 = CompositionFactory(name='composition2',
                                            nace='nace2')
        self.activitygroup1 = ActivityGroupFactory(keyflow=self.kic_obj)
        self.activity1 = ActivityFactory(activitygroup=self.activitygroup1)
        self.actor1 = ActorFactory(id=self.actor1id, activity=self.activity1)
        self.activitygroup2 = ActivityGroupFactory(keyflow=self.kic_obj)
        self.activity2 = ActivityFactory(activitygroup=self.activitygroup2)
        self.actor2 = ActorFactory(id=self.actor2id, activity=self.activity2)
        self.actor3 = ActorFactory(activity=self.activity2)
        self.act2act1 = Actor2ActorFactory(id=self.actor2actor1,
                                           origin=self.actor1,
                                           destination=self.actor2,
                                           keyflow=self.kic_obj,
                                           composition=self.comp1,
                                           process=self.process,
                                           amount=90
                                           )
        self.act2act2 = Actor2ActorFactory(id=self.actor2actor2,
                                           origin=self.actor2,
                                           destination=self.actor3,
                                           keyflow=self.kic_obj,
                                           composition=self.comp2,
                                           process=self.process,
                                           amount=30
                                           )
        self.obj = self.act2act1
        self.publicationic = PublicationInCasestudyFactory()
        self.pfrac1 = ProductFractionFactory(composition=self.comp1,
                                             material=self.mat_obj_1,
                                             publication=self.publicationic)
        self.pfrac2 = ProductFractionFactory(composition=self.comp1,
                                             material=self.mat_obj_2,
                                             publication=self.publicationic)
        self.pfrac3 = ProductFractionFactory(composition=self.comp2,
                                             material=self.mat_obj_1,
                                             publication=self.publicationic)
        self.pfrac4 = ProductFractionFactory(composition=self.comp2,
                                             material=self.mat_obj_2,
                                             publication=self.publicationic)


    def test_post_get(self):
        """
        Test if user can post without permission
        """
        filterdata = json.dumps([{
            'link': 'or',
            'functions': [
                {
                    'function': 'origin__activity__activitygroup__id__in',
                    'values': [self.activitygroup1.id, self.activitygroup2.id],
                }
            ]
        }])
        post_data1 = dict(aggregation_level=json.dumps(
            dict(origin='activitygroup', destination='activitygroup')),
                          materials=json.dumps(dict(aggregate=True,
                                                    ids=[self.material_1,
                                                        self.material_2,
                                                        self.material_3])),
                             filters=filterdata)
        post_data2 = dict(aggregation_level=json.dumps(
            dict(origin='activitygroup', destination='activitygroup')),
                          materials=json.dumps(dict(aggregate=False,
                                                    ids=[self.material_1])),
                                 filters=filterdata)
        url = '/api/casestudies/{}/keyflows/{}/actor2actor/?GET=true'.format(
            self.casestudy, self.kic_obj.id)

        # ToDo: THE ACTUAL TEST IS MISSING!!!!!


    def test_fractionflows(self):
        fc_before = len(FractionFlow.objects.all())
        url = self.url_key + '-list'
        n_fractions = len(self.post_data['composition']['fractions'])
        post_data = self.post_data.copy()
        post_data['amount'] = 1000
        response = self.post(url, **self.url_pks, data=post_data,
                             extra={'format': 'json'})
        id = response.json()['id']
        flow = Actor2Actor.objects.get(id=id)

        fc_after = len(FractionFlow.objects.all())
        assert fc_after - fc_before == n_fractions

        fraction_flows = FractionFlow.objects.filter(flow=flow)
        assert sum(fraction_flows.values_list('amount', flat=True)) \
               == flow.amount

        put_data = {'amount': 50000}
        url = self.url_key + '-detail'
        kwargs = {**self.url_pks, 'pk': id, }
        response = self.patch(url, **kwargs, data=put_data,
                              extra={'format': 'json'})
        # number of flowfractions should have stayed the same
        assert fc_after == len(FractionFlow.objects.all())
        flow = Actor2Actor.objects.get(id=id)
        # but with updated amounts
        fraction_flows = FractionFlow.objects.filter(flow=flow)
        assert sum(fraction_flows.values_list('amount', flat=True)) \
               == flow.amount

        # test cascaded deletion (flow deleted -> flowfractions deleted)
        flow.delete()
        assert len(FractionFlow.objects.all()) == fc_before


class Group2GroupInKeyflowInCaseStudyTest(BasicModelPermissionTest,
                                          APITestCase):
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
                            process=None
                            )
        cls.post_data = dict(origin=cls.origin,
                             destination=cls.destination,
                             composition=cls.comp_data,
                             process=None
                             )
        cls.patch_data = dict(origin=cls.origin,
                              destination=cls.destination,
                              composition=cls.comp_data,
                              process=None
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


class MaterialTest(BasicModelPermissionTest, APITestCase):
    material_1 = 1
    material_2 = 2
    material_3 = 3
    a2a_1 = 1
    a2a_2 = 2
    comp_1 = 1
    comp_2 = 2
    frac_1 = 1
    frac_2 = 2
    frac_3 = 3
    pub_1 = 1
    pub_2 = 2
    pub_3 = 3
    keyflowincasestudy = 5
    keyflow = 7
    casestudy = 4
    do_not_check = ['keyflow']


    def setUp(self):
        super().setUp()
        self.kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                                 casestudy=self.uic.casestudy,
                                                 keyflow__id=self.keyflow)
        self.comp_1_obj = CompositionFactory(id=self.comp_1)
        self.comp_2_obj = CompositionFactory(id=self.comp_2)
        self.a2a_1_obj = Actor2ActorFactory(id=self.a2a_1,
                                            composition=self.comp_1_obj)
        self.a2a_2_obj = Actor2ActorFactory(id=self.a2a_2,
                                            composition=self.comp_2_obj)
        self.mat_grandparent = MaterialFactory(id=self.material_1,
                                               keyflow=self.kic_obj)
        self.mat_parent = MaterialFactory(id=self.material_2,
                                          keyflow=self.kic_obj,
                                          parent=self.mat_grandparent)
        self.mat_child = MaterialFactory(id=self.material_3,
                                         keyflow=self.kic_obj,
                                         parent=self.mat_parent)
        self.obj = self.mat_grandparent
        self.frac_1_obj =  ProductFractionFactory(id=self.frac_1,
                                                  composition=self.comp_1_obj,
                                                  material=self.mat_parent,
                                                  publication__id=self.pub_1)
        #self.frac_2_obj =  ProductFractionFactory(id=self.frac_2,
                                                  #composition=self.comp_1_obj,
                                                  #material=self.\
                                                  #mat_grandparent,
                                                  #publication__id=self.pub_2)
        #self.frac_3_obj =  ProductFractionFactory(id=self.frac_3,
                                                  #composition=self.comp_2_obj,
                                                  #material=self.mat_parent,
                                                  #publication__id=self.pub_3)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "material"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.material_1)
        cls.put_data = dict(name='testname',
                            keyflow=cls.keyflowincasestudy,
                            level=1,
                            parent=None,
                            )
        cls.post_data = cls.put_data
        cls.patch_data = cls.put_data

    def test_filter_by_material(self):
        filtered = filter_by_material([self.mat_grandparent],
                                      Actor2Actor.objects)
        assert filtered.count() == 1
        assert filtered.first().id == 1

    def test_ancestor(self):
        args =  (self.mat_child, self.mat_parent, self.mat_grandparent)
        ancestor = self.mat_child.ancestor(*args)
        assert ancestor == self.mat_parent
        ancestor = self.mat_grandparent.ancestor(*args)
        assert ancestor == None

    def test_is_descendant(self):
        args =  (self.mat_child, self.mat_parent, self.mat_grandparent)
        descendand = self.mat_child.is_descendant(*args)
        assert descendand == True
        descendand = self.mat_grandparent.is_descendant(*args)
        assert descendand == False

    def test_delete(self):
        old_obj = self.obj
        self.obj = self.mat_child
        super().test_delete()
        self.obj = old_obj
        self.assertRaises(Exception, super().test_delete)
        x = 'breakpoint'


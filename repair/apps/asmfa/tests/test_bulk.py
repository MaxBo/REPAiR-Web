# -*- coding: utf-8 -*-

from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status
from repair.tests.test import LoginTestCase, AdminAreaTest

from repair.apps.asmfa.factories import (ActivityFactory,
                                         ActivityGroupFactory,
                                         )


class ActivitygroupImportTest(APITestCase):

    casestudy = 11
    keyflow = 23
    userincasestudy = 26
    user = 99

    filename_actg = 'T3.2_Activity_groups.tsv'
    filename_act = 'T3.2_Activities.tsv'
    filename_actor = 'T3.2_Actors.tsv'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uic = UserInCasestudyFactory(id=cls.userincasestudy,
                                             user__user__id=cls.user,
                                             user__user__username='Anonymus User',
                                             casestudy__id=cls.casestudy)
        cls.kic = KeyflowInCasestudyFactory(id=cls.keyflow,
                                            casestudy=cls.uic.casestudy)

        cls.url_key = "activitygroup"
        cls.url_pks = dict(casestudy_pk=cls.uic.casestudy,
                           keyflow_pk=cls.kic.id)

    def setUp(self):
        super().setUp()
        # create another activitygroup
        ActivityGroupFactory(keyflow_id=self.keyflow, name='Construction', code='F')
        ActivityGroupFactory(keyflow_id=self.keyflow, name='Other', code='E')
        ActivityGroupFactory(keyflow_id=self.keyflow, name='Export', code='WE')
        ActivityGroupFactory(keyflow_id=self.keyflow, name='Import', code='R')

    def test_bulk_ag(self):
        """
        Test if user can post without permission
        """
        pass
        #filterdata = json.dumps({file: self.filename_actg})
        #post_data1 = dict(aggregation_level=json.dumps(
            #dict(origin='activitygroup', destination='activitygroup')),
                          #materials=json.dumps(dict(aggregate=True,
                                                    #ids=[self.material_1,
                                                        #self.material_2,
                                                        #self.material_3])),
                             #filters=filterdata)
        #post_data2 = dict(aggregation_level=json.dumps(
            #dict(origin='activitygroup', destination='activitygroup')),
                          #materials=json.dumps(dict(aggregate=False,
                                                    #ids=[self.material_1])),
                                 #filters=filterdata)
        #url = '/api/casestudies/{}/keyflows/{}/actor2actor/?GET=true'.format(
            #self.casestudy, self.kic_obj.id)
        #for post_data in [post_data1, post_data2]:
            #response = self.post(
                #url,
                #data=post_data,
                #extra={'format': 'json'})
            #self.response_200()

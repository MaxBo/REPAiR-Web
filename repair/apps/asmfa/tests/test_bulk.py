# -*- coding: utf-8 -*-

from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status
from repair.tests.test import LoginTestCase, AdminAreaTest
from django.urls import reverse
import os
import pandas as pd

from repair.apps.asmfa.factories import (ActivityFactory,
                                         ActivityGroupFactory,
                                         UserInCasestudyFactory,
                                         KeyflowInCasestudyFactory
                                         )
from repair.apps.asmfa.models import ActivityGroup, Activity

testdata_folder = 'data'


class BulkImportActivitygroupTest(LoginTestCase, APITestCase):

    filename_actg = 'T3.2_Activity_groups.tsv'
    filename_act = 'T3.2_Activities.tsv'
    filename_actor = 'T3.2_Actors.tsv'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.keyflow = cls.kic
        cls.casestudy = cls.uic.casestudy

    def setUp(self):
        super().setUp()
        # create another activitygroup
        ActivityGroupFactory(keyflow=self.keyflow, name='Construction', code='F')
        ActivityGroupFactory(keyflow=self.keyflow, name='Other', code='E')
        ActivityGroupFactory(keyflow=self.keyflow, name='Export', code='WE')
        ActivityGroupFactory(keyflow=self.keyflow, name='Import', code='R')

    def test_bulk_ag(self):
        """
        Test if user can post without permission
        """
        url = reverse('activitygroup-list',
                      kwargs={'casestudy_pk': self.casestudy.id,
                              'keyflow_pk': self.keyflow.id})
        file_path_ag = os.path.join(os.path.dirname(__file__),
                                    testdata_folder,
                                    self.filename_actg)
        data = {
            'bulk_upload' : open(file_path_ag, 'rb'),
        }

        existing_ags = ActivityGroup.objects.filter(keyflow=self.kic)
        existing_codes = list(existing_ags.values_list('code', flat=True))

        encoding = 'utf8'
        df_file_ags = pd.read_csv(file_path_ag, sep='\t')
        df_file_ags = df_file_ags.rename(
            columns={c: c.lower() for c in df_file_ags.columns})
        file_codes = df_file_ags['code']
        new_codes = [c for c in file_codes if c not in existing_codes]

        res = self.client.post(url, data)
        assert res.status_code == 201

        # assert that the number of activities matches
        all_ag = ActivityGroup.objects.filter(keyflow_id=self.kic.id)
        assert len(all_ag) == len(existing_codes) + len(new_codes)

        # assert that the Name matches in all values
        for row in df_file_ags.itertuples(index=False):
            ag = ActivityGroup.objects.get(keyflow=self.keyflow,
                                           code=row.code)
            assert ag.name == row.name

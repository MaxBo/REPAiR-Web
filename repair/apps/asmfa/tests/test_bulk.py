# -*- coding: utf-8 -*-

import os
from unittest import skip
import pandas as pd
from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status
from repair.tests.test import LoginTestCase, AdminAreaTest
from django.urls import reverse

from repair.apps.asmfa.factories import (ActivityFactory,
                                         ActivityGroupFactory,
                                         UserInCasestudyFactory,
                                         KeyflowInCasestudyFactory
                                         )
from repair.apps.asmfa.models import ActivityGroup, Activity


class BulkImportActivitygroupTest(LoginTestCase, APITestCase):

    testdata_folder = 'data'
    filename_actg = 'T3.2_Activity_groups.tsv'
    filename_act = 'T3.2_Activities.tsv'
    filename_actor = 'T3.2_Actors.tsv'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.keyflow = cls.kic
        cls.casestudy = cls.uic.casestudy

        cls.ag_url = reverse('activitygroup-list',
                             kwargs={'casestudy_pk': cls.casestudy.id,
                                     'keyflow_pk': cls.keyflow.id})
        cls.ac_url = reverse('activity-list',
                             kwargs={'casestudy_pk': cls.casestudy.id,
                                     'keyflow_pk': cls.keyflow.id})

    def setUp(self):
        super().setUp()
        # create another activitygroup
        ActivityGroupFactory(keyflow=self.keyflow, name='Construction', code='F')
        ActivityGroupFactory(keyflow=self.keyflow, name='Other', code='E')
        ActivityGroupFactory(keyflow=self.keyflow, name='Export', code='WE')
        ActivityGroupFactory(keyflow=self.keyflow, name='Import', code='R')

        ag_f = ActivityGroup.objects.get(code='F')
        ActivityFactory(activitygroup=ag_f, name='should_be_updated', nace='F-4110')
        ActivityFactory(activitygroup=ag_f, name='shouldnt_be_updated', nace='F-007')

    def test_bulk_group(self):
        """
        Test if user can post without permission
        """
        file_path_ag = os.path.join(os.path.dirname(__file__),
                                    self.testdata_folder,
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

        res = self.client.post(self.ag_url, data)
        assert res.status_code == 201
        assert res.json()['count'] == len(file_codes)

        # assert that the number of activities matches
        all_ag = ActivityGroup.objects.filter(keyflow_id=self.kic.id)
        assert len(all_ag) == len(existing_codes) + len(new_codes)

        # assert that the Name matches in all values
        for row in df_file_ags.itertuples(index=False):
            ag = ActivityGroup.objects.get(keyflow=self.keyflow,
                                           code=row.code)
            assert ag.name == row.name

    def test_bulk_activity(self):
        """Test that activity matches activitygroup"""
        url = reverse('activity-list',
                      kwargs={'casestudy_pk': self.casestudy.id,
                              'keyflow_pk': self.keyflow.id})
        file_path_ac = os.path.join(os.path.dirname(__file__),
                                    self.testdata_folder,
                                    self.filename_act)
        data = {
            'bulk_upload' : open(file_path_ac, 'rb'),
        }

        existing_acs = Activity.objects.filter(activitygroup__keyflow=self.kic)
        existing_nace = list(existing_acs.values_list('nace', flat=True))

        encoding = 'cp1252'
        df_file_ags = pd.read_csv(file_path_ac, sep='\t', encoding=encoding)
        df_file_ags = df_file_ags.rename(
            columns={c: c.lower() for c in df_file_ags.columns})
        file_nace = df_file_ags['nace']
        new_nace = [c for c in file_nace if c not in existing_nace]

        res = self.client.post(self.ac_url, data)
        assert res.status_code == 201

        # assert that the number of activities matches
        all_ac = Activity.objects.filter(activitygroup__keyflow=self.kic)
        assert len(all_ac) == len(existing_nace) + len(new_nace)

        # assert that the Name matches in all values
        for row in df_file_ags.itertuples(index=False):
            # ToDo: different test case if activitygroups don't exist
            ag = ActivityGroup.objects.get(code=row.ag)
            ac = Activity.objects.get(activitygroup=ag,
                                      nace=row.nace)
            assert ac.name == row.name

    @skip('not implemented yet')
    def test_actor_matches_activity(self):
        """Test that actor matches activity"""

    @skip('not implemented yet')
    def test_bulk_actors(self):
        """
        Test that flow/stock matches
        activity and material and composition
        """
    @skip('not implemented yet')
    def test_composition_adds_to_100_percent(self):
        """Test that material compostitions add up to 100 %"""

    @skip('not implemented yet')
    def test_households_in_admin_unit(self):
        """
        Test that Household administrative units
        are in the list of Administrative Units
        """

    @skip('not implemented yet')
    def test_tabs_in_text(self):
        """tabs in text"""

    @skip('not implemented yet')
    def test_duplicate_entries(self):
        """Test if duplicate entries in the same table"""

    @skip('hard_to_test')
    def test_amount_in_tons(self):
        """Test if amount is given in tons/year"""

    @skip('not implemented yet')
    def test_missing_data_sources(self):
        """Test if data sources are given"""



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
                                         ActorFactory,
                                         UserInCasestudyFactory,
                                         KeyflowInCasestudyFactory,
                                         CompositionFactory,
                                         Actor2ActorFactory,
                                         MaterialFactory
                                         )
from repair.apps.asmfa.models import ActivityGroup, Activity, Actor, Material
from repair.apps.publications.factories import (PublicationFactory,
                                                PublicationInCasestudyFactory)


class BulkImportNodesTest(LoginTestCase, APITestCase):

    testdata_folder = 'data'
    filename_actg = 'T3.2_Activity_groups.tsv'
    filename_actg_csv = 'T3.2_Activity_groups.csv'
    filename_actg_missing_col = 'T3.2_Activity_groups_missing_col.tsv'
    filename_act = 'T3.2_Activities.tsv'
    filename_act_missing_rel = 'T3.2_Activities_missing_relation.tsv'
    filename_act_missing_rel_xlsx = 'T3.2_Activities_missing_relation.xlsx'
    filename_actor = 'T3.2_Actors.tsv'
    filename_actor_w_errors = 'T3.2_Actors_w_errors.tsv'
    filename_actor_w_errors_xlsx = 'T3.2_Actors_w_errors.xlsx'
    filename_locations = 'test_adminloc.csv'

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
        cls.actor_url = reverse('actor-list',
                                kwargs={'casestudy_pk': cls.casestudy.id,
                                        'keyflow_pk': cls.keyflow.id})
        cls.location_url = reverse('administrativelocation-list',
                                   kwargs={'casestudy_pk': cls.casestudy.id,
                                           'keyflow_pk': cls.keyflow.id})

    def setUp(self):
        super().setUp()
        # create another activitygroup
        ag_f = ActivityGroupFactory(keyflow=self.keyflow,
                                    name='Construction', code='F')
        ActivityGroupFactory(keyflow=self.keyflow,
                             name='Some stuff, no idea', code='G')
        ActivityGroupFactory(keyflow=self.keyflow,
                             name='Other', code='E')
        ActivityGroupFactory(keyflow=self.keyflow,
                             name='Export', code='WE')
        ActivityGroupFactory(keyflow=self.keyflow,
                             name='Import', code='R')

        af = ActivityFactory(activitygroup=ag_f, name='should_be_updated',
                             nace='4110')
        ActivityFactory(activitygroup=ag_f,
                        name='Collection of non-hazardous waste', nace='3811')
        ActivityFactory(activitygroup=ag_f,
                        name='Collection of hazardous waste', nace='3812')
        ActivityFactory(activitygroup=ag_f,
                        name='shouldnt_be_updated', nace='F-007')

        ActorFactory(activity=af, BvDid='NL000000029386')
        ActorFactory(activity=af, BvDid='NL32063450')

    def test_bulk_group(self):
        """
        test bulk upload activitygroups
        """
        for fn, sep in [(self.filename_actg, '\t'),
                        (self.filename_actg_csv, ';')]:
            file_path_ag = os.path.join(os.path.dirname(__file__),
                                        self.testdata_folder,
                                        fn)
            data = {
                'bulk_upload' : open(file_path_ag, 'rb'),
            }

            existing_ags = ActivityGroup.objects.filter(keyflow=self.kic)
            existing_codes = list(existing_ags.values_list('code', flat=True))

            encoding = 'utf8'
            df_file_ags = pd.read_csv(file_path_ag, sep=sep)
            df_file_ags = df_file_ags.rename(
                columns={c: c.lower() for c in df_file_ags.columns})
            file_codes = df_file_ags['code']
            new_codes = [c for c in file_codes if c not in existing_codes]

            res = self.client.post(self.ag_url, data)
            res_json = res.json()
            assert res.status_code == 201
            assert res_json['count'] == len(file_codes)
            assert len(res_json['created']) == len(new_codes)

            # assert that the number of activities matches
            all_ag = ActivityGroup.objects.filter(keyflow_id=self.kic.id)
            assert len(all_ag) == len(existing_codes) + len(new_codes)

            # assert that the Name matches in all values
            for row in df_file_ags.itertuples(index=False):
                ag = ActivityGroup.objects.get(keyflow=self.keyflow,
                                               code=row.code)
                assert ag.name == row.name

    def test_bulk_group_errors(self):
        """
        test errors in upload files
        """
        file_path = os.path.join(os.path.dirname(__file__),
                                 self.testdata_folder,
                                 self.filename_actg_missing_col)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }
        res = self.client.post(self.ag_url, data)
        assert res.status_code == 400

    def test_bulk_activity_errors(self):
        file_path = os.path.join(os.path.dirname(__file__),
                                 self.testdata_folder,
                                 self.filename_act_missing_rel)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }
        res = self.client.post(self.ac_url, data)
        assert res.status_code == 400

    def test_excel(self):
        file_path = os.path.join(os.path.dirname(__file__),
                                 self.testdata_folder,
                                 self.filename_act_missing_rel_xlsx)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }
        res = self.client.post(self.ac_url, data)
        assert res.status_code == 400

    def test_bulk_activity(self):
        """Test bulk upload activities"""
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
        new_nace = [c for c in file_nace if str(c) not in existing_nace]

        res = self.client.post(self.ac_url, data)
        assert res.status_code == 201
        res_json = res.json()
        assert res_json['count'] == len(file_nace)
        assert len(res_json['created']) == len(new_nace)

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

    def test_bulk_actors(self):
        """Test bulk upload actors"""
        file_path = os.path.join(os.path.dirname(__file__),
                                self.testdata_folder,
                                self.filename_actor)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }

        res = self.client.post(self.actor_url, data)
        assert res.status_code == 201

    def test_bulk_actor_errors(self):
        """Test that activity matches activitygroup"""
        file_path = os.path.join(os.path.dirname(__file__),
                                self.testdata_folder,
                                self.filename_actor_w_errors_xlsx)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }

        res = self.client.post(self.actor_url, data)
        assert res.status_code == 400

    def test_bulk_locations(self):
        """Test bulk upload actors"""
        file_path = os.path.join(os.path.dirname(__file__),
                                 self.testdata_folder,
                                 self.filename_locations)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }

        res = self.client.post(self.location_url, data)
        assert res.status_code == 201

    @skip('not implemented yet')
    def test_actor_matches_activity(self):
        """Test that actor matches activity"""

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


class BulkImportFlowsTest(LoginTestCase, APITestCase):

    testdata_folder = 'data'
    filename_a2a = 'T3.2_Flows_actor2actor.tsv'
    filename_astock = 'T3.2_Flows_actorstock.tsv'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.keyflow = cls.kic
        cls.casestudy = cls.uic.casestudy

        cls.a2a_url = reverse('actor2actor-list',
                              kwargs={'casestudy_pk': cls.casestudy.id,
                                      'keyflow_pk': cls.keyflow.id})

        cls.astock_url = reverse('actorstock-list',
                                 kwargs={'casestudy_pk': cls.casestudy.id,
                                         'keyflow_pk': cls.keyflow.id})
        # workaround, don't want to tests any permissions here
        #cls.uic.user.user.is_superuser = True
        #cls.uic.user.user.save()

    def setUp(self):
        super().setUp()
        # create another activitygroup
        ag = ActivityGroupFactory(keyflow=self.keyflow, name='A', code='A')
        af = ActivityFactory(activitygroup=ag, name='B', nace='123')

        ac_1 = ActorFactory(activity=af, BvDid='WK036306')
        ac_2 = ActorFactory(activity=af, BvDid='WK036307')
        ActorFactory(activity=af, BvDid='WK036308')
        ActorFactory(activity=af, BvDid='WK036309')
        ac_3 = ActorFactory(activity=af, BvDid='NL59307803')

        CompositionFactory(name='RES @Urbanisation lvl 1')

        a = PublicationFactory(citekey='cbs2018', title='sth')
        PublicationInCasestudyFactory(casestudy=self.casestudy,
                                      publication=a)

        Actor2ActorFactory(origin=ac_1, destination=ac_2, keyflow=self.keyflow)
        Actor2ActorFactory(origin=ac_1, destination=ac_3, keyflow=self.keyflow)

    def test_bulk_flow(self):
        """Test file-based upload of actor2actor"""
        file_path = os.path.join(os.path.dirname(__file__),
                                self.testdata_folder,
                                self.filename_a2a)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }

        res = self.client.post(self.a2a_url, data)
        assert res.status_code == 201

    def test_bulk_stock(self):
        """Test file-based upload of actor2actor"""
        file_path = os.path.join(os.path.dirname(__file__),
                                self.testdata_folder,
                                self.filename_astock)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }

        res = self.client.post(self.astock_url, data)
        assert res.status_code == 201


class BulkImportMaterialsTest(LoginTestCase, APITestCase):
    testdata_folder = 'data'
    filename_materials = 'materials.tsv'
    filename_materials_w_errors = 'materials_w_errors.tsv'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.keyflow = cls.kic
        cls.casestudy = cls.uic.casestudy

        cls.mat_url = reverse('material-list',
                              kwargs={'casestudy_pk': cls.casestudy.id,
                                      'keyflow_pk': cls.keyflow.id})

    def setUp(self):
        super().setUp()
        MaterialFactory(name='Mat 1', keyflow=self.keyflow)
        # this one is a 'default' material without keyflow and duplicate
        # to one in the file, the keyflow related one should be preferred
        MaterialFactory(name='a')
        MaterialFactory(name='b')

    def test_bulk_materials(self):
        file_path = os.path.join(os.path.dirname(__file__),
                                self.testdata_folder,
                                self.filename_materials)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }

        res = self.client.post(self.mat_url, data)
        assert res.status_code == 201

    def test_bulk_materials_errors(self):
        file_path = os.path.join(os.path.dirname(__file__),
                                self.testdata_folder,
                                self.filename_materials_w_errors)
        n_before = len(Material.objects.all())
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }

        res = self.client.post(self.mat_url, data)
        assert res.status_code == 400
        n_after = len(Material.objects.all())
        assert n_after == n_before


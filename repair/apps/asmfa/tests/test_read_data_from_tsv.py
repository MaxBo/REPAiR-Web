# -*- coding: utf-8 -*-

import os
import pandas as pd
import tablib
from django.urls import reverse
from django_pandas.io import read_frame
from test_plus import APITestCase
from rest_framework import status
from import_export import resources

from repair.tests.test import LoginTestCase, AdminAreaTest
from repair.apps.login.factories import UserInCasestudyFactory

from repair.apps.asmfa.factories import (KeyflowInCasestudyFactory,
                                         ActivityGroupFactory)
from ..models import ActivityGroup, Activity

testdata_folder = 'data'

from import_export.fields import Field

class ActivitygroupResource(resources.ModelResource):
    keyflow = Field(attribute='keyflow', default=22)
    id = Field(attribute='id', default=22)

    class Meta:
        model = ActivityGroup


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

    def test_import_table(self):
        """
        Test if the test-data-table can be imported successfully
        """
        file_path_ag = os.path.join(os.path.dirname(__file__),
                                    testdata_folder,
                                    self.filename_actg)
        # read csv to Dataframe
        index_col = ['code']
        encoding = 'utf8'
        df_ag_new = pd.read_csv(file_path_ag, sep='\t')
        df_ag_new = df_ag_new.\
            rename(columns={c: c.lower() for c in df_ag_new.columns}).\
            set_index(index_col)

        # get existing activitygroups of keyflow
        qs = ActivityGroup.objects.filter(keyflow_id=self.kic.id)
        df_ag_old = read_frame(qs, index_col=['code'])

        existing_ag = df_ag_new.merge(df_ag_old,
                                      left_index=True,
                                      right_index=True,
                                      how='left',
                                      indicator=True,
                                      suffixes=['', '_old'])
        new_ag = existing_ag.loc[existing_ag._merge=='left_only'].reset_index()
        idx_both = existing_ag.loc[existing_ag._merge=='both'].index

        # set the KeyflowInCasestudy for the new rows
        new_ag.loc[:, 'keyflow'] = self.kic

        # skip columns, that are not needed
        field_names = [f.name for f in ActivityGroup._meta.fields]
        drop_cols = []
        for c in new_ag.columns:
            if not c in field_names or c.endswith('_old'):
                drop_cols.append(c)
        drop_cols.append('id')
        new_ag.drop(columns=drop_cols, inplace=True)

        # set default values for columns not provided
        defaults = {col: ActivityGroup._meta.get_field(col).default
                    for col in new_ag.columns}
        new_ag = new_ag.fillna(defaults)

        # create the new rows
        ags = []
        for row in new_ag.itertuples(index=False):
            row_dict = row._asdict()
            ag = ActivityGroup(**row_dict)
            ags.append(ag)
        ActivityGroup.objects.bulk_create(ags)

        # update existing values
        ignore_cols = ['id', 'keyflow']

        df_updated = df_ag_old.loc[idx_both]
        df_updated.update(df_ag_new)
        for row in df_updated.reset_index().itertuples(index=False):
            ag = ActivityGroup.objects.get(keyflow_id=self.kic.id,
                                           code=row.code)
            for c, v in row._asdict().items():
                if c in ignore_cols:
                    continue
                setattr(ag, c, v)
            ag.save()

        # assert that the number of activities matches
        all_ag = ActivityGroup.objects.filter(keyflow_id=self.kic.id)
        assert len(all_ag) == len(df_ag_old) + len(new_ag)

        # assert that the Name matches in all values
        for row in df_ag_new.reset_index().itertuples(index=False):
            ag = ActivityGroup.objects.get(keyflow_id=self.kic.id,
                                           code=row.code)
            assert ag.name == row.name


    def test_add_activities(self):
        """Test adding activities that have an invalid activity-group"""
        file_path_act = os.path.join(os.path.dirname(__file__),
                                     testdata_folder,
                                     self.filename_act)
        index_col = 'nace'
        encoding = 'cp1252'
        # read csv to Dataframe
        df_act_new = pd.read_csv(file_path_act, sep='\t', encoding=encoding)
        df_act_new = df_act_new.\
            rename(columns={c: c.lower() for c in df_act_new.columns}).\
            set_index(index_col)

        # get existing activitygroups of keyflow
        qs = ActivityGroup.objects.filter(keyflow_id=self.kic.id)
        df_ag = read_frame(qs, index_col=['code'])

        # get existing activities of keyflow
        qs = Activity.objects.filter(activitygroup__keyflow_id=self.kic.id)
        df_act_old = read_frame(qs, index_col=[index_col])

        # check if an activitygroup exist for each activity
        existing_ag = df_act_new.merge(df_ag,
                                       left_on='ag',
                                       right_index=True,
                                       how='left',
                                       indicator=True,
                                       suffixes=['', '_old'])
        missing_activitygroups = existing_ag.loc[
            existing_ag._merge=='left_only']
        assert len(missing_activitygroups) == 1

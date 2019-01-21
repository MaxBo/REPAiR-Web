# -*- coding: utf-8 -*-

import os
from unittest import skip
import pandas as pd
from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status
from repair.tests.test import LoginTestCase
from django.urls import reverse

from repair.apps.studyarea.factories import AdminLevelsFactory
from repair.apps.studyarea.models import Area, AdminLevels


class BulkImportAreaTest(LoginTestCase, APITestCase):
    testdata_folder = 'data'
    filename_levels = 'adminlevels.tsv'
    filename_levels_w_errors = 'adminlevels_errors.tsv'
    filename_continents = 'continents.tsv'
    filename_areas = 'continents.tsv'
    filename_countries_broken = 'countries_broken_geom.csv'
    filename_continents_intersect = 'continents_self_intersect.tsv'
    filename_countries_intersect = 'countries_self_intersect.csv'
    filename_countries = 'countries.csv'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.casestudy = cls.uic.casestudy

        cls.level_url = reverse('adminlevels-list',
                                kwargs={'casestudy_pk': cls.casestudy.id})
        cls.area_url = reverse('area-list',
                               kwargs={'casestudy_pk': cls.casestudy.id})

    def setUp(self):
        super().setUp()
        AdminLevelsFactory(level=1, name='World', casestudy=self.casestudy)
        AdminLevelsFactory(level=2, name='Continent', casestudy=self.casestudy)
        AdminLevelsFactory(level=3, name='Country', casestudy=self.casestudy)

    def test_bulk_levels(self):
        file_path = os.path.join(os.path.dirname(__file__),
                                self.testdata_folder,
                                self.filename_levels)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }
        res = self.client.post(self.level_url, data)
        assert res.status_code == 201

    def test_bulk_levels_errors(self):
        file_path = os.path.join(os.path.dirname(__file__),
                                self.testdata_folder,
                                self.filename_levels_w_errors)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }
        n_before = len(AdminLevels.objects.all())
        res = self.client.post(self.level_url, data)
        assert res.status_code == 400
        assert len(AdminLevels.objects.all()) == n_before

    def test_bulk_areas(self):
        file_path = os.path.join(os.path.dirname(__file__),
                                self.testdata_folder,
                                self.filename_continents)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
        }
        res = self.client.post(self.area_url, data)
        assert res.status_code == 201
        file_path = os.path.join(os.path.dirname(__file__),
                                self.testdata_folder,
                                self.filename_countries)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
            'encoding': 'utf-8',
        }
        res = self.client.post(self.area_url, data)
        assert res.status_code == 201

    def test_bulk_areas_errors(self):
        file_path = os.path.join(os.path.dirname(__file__),
                                self.testdata_folder,
                                self.filename_countries_broken)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
            'encoding': 'utf-8',
        }
        res = self.client.post(self.area_url, data)
        assert res.status_code == 400
        file_path = os.path.join(os.path.dirname(__file__),
                                self.testdata_folder,
                                self.filename_continents_intersect)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
            'encoding': 'utf-8',
        }
        res = self.client.post(self.area_url, data)
        assert res.status_code == 400
        file_path = os.path.join(os.path.dirname(__file__),
                                self.testdata_folder,
                                self.filename_countries_intersect)
        data = {
            'bulk_upload' : open(file_path, 'rb'),
            'encoding': 'utf-8',
        }
        res = self.client.post(self.area_url, data)
        assert res.status_code == 400



# -*- coding: utf-8 -*-

from django.urls import reverse
from test_plus import APITestCase
from repair.tests.test import BasicModelTest


from repair.apps.publications.factories import *


class PublicationInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 1
    publication = 11
    pup_type = 'Handwriting'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cs_url = cls.baseurl + reverse('casestudy-detail',
                                   kwargs=dict(pk=cls.casestudy))

        cls.url_key = "publicationincasestudy"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.publication)

        cls.put_data = dict(title='new_put_title',
                             )
        cls.post_data = dict(title='new_title',
                             type=cls.pup_type)

        cls.patch_data = dict(title='patchtest_title')

    def setUp(self):
        super().setUp()
        self.obj = PublicationInCasestudyFactory(casestudy=self.uic.casestudy,
                                                 publication__id=self.publication,
                                                 publication__type__title=self.pup_type)

# -*- coding: utf-8 -*-

from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status
from repair.tests.test import BasicModelPermissionTest, LoginTestCase
from repair.apps.statusquo.factories import ChallengeFactory


class ChallengeTest(BasicModelPermissionTest, APITestCase):

    casestudy = 17
    challenge = 20

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "challenge"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.challenge)
        cls.post_data = dict(text='test challenge')
        cls.put_data = cls.post_data
        cls.patch_data = cls.post_data

    def setUp(self):
        super().setUp()
        self.obj = ChallengeFactory(casestudy=self.uic.casestudy,
                              id=self.challenge)
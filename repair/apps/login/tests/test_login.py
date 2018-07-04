# -*- coding: UTF-8 -*-
import unittest
from django.test import TestCase
from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status

from repair.apps.login.models import CaseStudy, User, Profile, UserInCasestudy
from repair.apps.login.factories import (UserFactory,
                                         GroupFactory,
                                         UserInCasestudyFactory,
                                         ProfileFactory,
                                         CaseStudyFactory)
from repair.tests.test import BasicModelPermissionTest, CompareAbsURIMixin
from django.contrib.auth.models import Permission


class ModelTest(TestCase):

    def test_user_creation(self):
        # New user created
        user = User.objects.create(
            username="horst",
            password="django-tutorial",
            email='horst@gmail.com')
        # Check that a Profile instance has been crated
        self.assertIsInstance(user.profile, Profile)
        # Call the save method of the user to activate the signal
        # again, and check that it doesn't try to create another
        # profile instace
        user.save()
        self.assertIsInstance(user.profile, Profile)

    def test_profile_creation(self):
        profile = ProfileFactory()
        # should use the default username of the UserFactory
        self.assertEqual(str(profile), profile.user.username)

        # should use the provided username
        profile = ProfileFactory(user__username='Adele')
        self.assertEqual(str(profile), "Adele")

    def test_string_representation(self):
        casestudy = CaseStudy(name="Liège")
        self.assertEqual(str(casestudy), "Liège")

        user = UserFactory(username="Markus")
        self.assertEqual(str(user.profile), "Markus")

        uic = UserInCasestudy(user=user.profile, casestudy=casestudy)
        self.assertEqual(str(uic), "Markus (Liège)")

    def test_casestudies_of_profile(self):
        casestudy_hh = CaseStudyFactory(name='Hamburg')
        casestudy_ams = CaseStudyFactory(name='Amsterdam')
        casestudies = [casestudy_hh, casestudy_ams]
        user = ProfileFactory()
        user_in_hh = UserInCasestudyFactory(user=user,
                                            casestudy=casestudy_hh)
        user_in_ams = UserInCasestudyFactory(user=user,
                                             casestudy=casestudy_ams)

        # assert that the user has the correct casestudies assigned
        self.assertEqual([(cs.id, cs.name) for cs in user.casestudies.all()],
                         [(cs.id, cs.name) for cs in casestudies])


class CasestudyTest(BasicModelPermissionTest, APITestCase):

    url_key = "casestudy"
    url_pks = dict()
    url_pk = dict(pk=1)
    post_data = dict(name='posttestname')
    put_data = {'name': 'puttestname', }
    patch_data = dict(name='patchtestname')

    def test_post(self):
        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data)
        for key in self.post_data:
            if key not in response.data.keys() or key in self.do_not_check:
                continue
            assert response.data[key] == self.post_data[key]

        # get
        new_id = response.data['id']
        url = self.url_key + '-detail'

        # casestudy is new -> noone may access it
        response = self.get(url, pk=new_id, **self.url_pks)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # grant access to new casestudy
        casestudy = CaseStudy.objects.get(id=new_id)
        casestudy.userincasestudy_set.add(self.uic)
        response = self.get_check_200(url, pk=new_id, **self.url_pks)

    def setUp(self):
        super().setUp()
        self.obj = self.kic.casestudy

    def test_session(self):
        casestudy_name = self.obj.name

        # at the beginning, no casestudy is selected
        casestudy = self.client.session.get('casestudy', None)
        assert casestudy is None

        # selecting a casestudy by posting to /login/session/
        url = '/session/'
        self.post(url, data={'casestudy': casestudy_name, })
        casestudy = self.client.session.get('casestudy', None)
        assert casestudy == casestudy_name

        # getting the selected casestudy
        response = self.get_check_200(url)
        assert response.json().get('casestudy', None) == casestudy_name


class UserInCasestudyTest(BasicModelPermissionTest, APITestCase):

    casestudy = 17
    user = 20

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "userincasestudy"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.user)
        cls.post_data = dict(role="role for testing")
        cls.put_data = dict(role="role for testing", user=cls.user)
        cls.patch_data = dict(role="role for testing")

    def setUp(self):
        super().setUp()
        self.obj = self.uic

    def test_delete(self):
        kwargs = {**self.url_pks, 'pk': self.obj.pk, }
        url = self.url_key + '-detail'
        response = self.get_check_200(url, **kwargs)

        # list all users in the casestudy
        response = self.get_check_200('userincasestudy-list', **self.url_pks)

        # delete is not allowed
        response = self.delete(url, **kwargs)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # delete manually
        uic = UserInCasestudy.objects.get(pk=self.obj.pk)
        uic.delete()
        response = self.get('userincasestudy-list', **self.url_pks)

        # after removing user
        # the casestudy is not permitted to access for this user any more
        assert response.status_code == status.HTTP_403_FORBIDDEN
        self.response_403()

    @unittest.skip('no Post possible')
    def test_post(self):
        """no Post"""

    @unittest.skip('no Post possible')
    def test_post_permission(self):
        """no Post"""

    @unittest.skip('no Delete possible')
    def test_delete_permission(self):
        """no Delete"""

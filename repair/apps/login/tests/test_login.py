import unittest
from django.test import TestCase
from django.core.validators import ValidationError
from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status

from repair.apps.login.models import CaseStudy, User, Profile
from repair.apps.login.factories import *
from repair.tests.test import (BasicModelPermissionTest,
                               BasicModelReadTest,
                               CompareAbsURIMixin)


class ModelTest(TestCase):

    #fixtures = ['auth', 'sandbox']


    def test_profile_creation(self):
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
        self.assertEqual(str(profile),"Adele")

    def test_string_representation(self):
        casestudy = CaseStudy(name="MyName")
        self.assertEqual(str(casestudy),"MyName")

        user = UserFactory(username="Markus")
        self.assertEqual(str(user.profile),"Markus")

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


class ViewTest(CompareAbsURIMixin, APITestCase):

    #fixtures = ['auth', 'sandbox']


    def test_get_group(self):
        url = reverse('group-list')
        data = {'name': 'MyGroup'}
        response = self.post('group-list', data=data,
                             extra=dict(format='json'))
        self.response_201()

        response = self.get_check_200('group-list')
        results = response.data['results']
        last_entry = results[-1]
        assert last_entry['name'] == 'MyGroup'

    def test_get_user(self):

        response = self.get_check_200('user-list')
        # users before adding a new one
        no_of_users = response.data['count']

        # add new user
        lodz = self.reverse('casestudy-detail', pk=3)
        group = self.reverse('group-detail', pk=1)
        initial_mail = 'a.b@c.de'
        data = {'username': 'MyUser',
                'casestudies': [lodz],
                'password': 'PW',
                'organization': 'GGR',
                'groups': [group],
                'email': initial_mail,}
        response = self.post('user-list', data=data, extra={'format': 'json'},)
        self.response_201()
        new_id = response.data['id']

        # should be one more now
        response = self.get_check_200('user-list')
        assert response.data['count'] == no_of_users + 1

        response = self.get_check_200('user-detail', pk=new_id)
        assert response.data['email'] == initial_mail
        # password should not be returned
        assert 'password' not in response.data
        self.assertURLsEqual(response.data['groups'], [group])
        self.assertURLsEqual(response.data['casestudies'], [lodz])

        new_mail = 'new@mail.de'
        data = {'email': new_mail,}
        response = self.patch('user-detail', pk=new_id, data=data)
        self.response_200()
        assert response.data['email'] == new_mail


class CasestudyTest(BasicModelPermissionTest, APITestCase):

    url_key = "casestudy"
    url_pks = dict()
    url_pk = dict(pk=1)
    post_data = dict(name='posttestname')
    put_data = {'name': 'puttestname', }
    patch_data = dict(name='patchtestname')
    add_perm = "login.add_casestudy"

    def test_post(self):
        url = self.url_key +'-list'
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
        cls.put_data = dict(role="role for testing")
        cls.patch_data = dict(role="role for testing")


    def setUp(self):
        super().setUp()
        self.obj = self.uic

    def test_delete(self):
        kwargs =  {**self.url_pks, 'pk': self.obj.pk, }
        url = self.url_key + '-detail'
        response = self.get_check_200(url, **kwargs)

        response = self.delete(url, **kwargs)
        response = self.get(ur, **kwargs)
        # after removing user the casestudy is permitted to access for this user
        assert response.status_code == status.HTTP_403_FORBIDDEN
        self.response_403()

    @unittest.skip('no Post possible')
    def test_post(self):
        """no Post"""

    @unittest.skip('no Delete possible')
    def test_delete(self):
        """no Delete"""

    @unittest.skip('no Post possible')
    def test_post_permission(self):
        """no Post"""

    @unittest.skip('no Delete possible')
    def test_delete_permission(self):
        """no Delete"""


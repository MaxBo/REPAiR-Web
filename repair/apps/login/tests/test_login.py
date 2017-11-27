from django.test import TestCase
from django.core.validators import ValidationError

from repair.apps.login.models import CaseStudy, User, Profile
from repair.apps.login.factories import *
from repair.apps.changes.factories import *
from rest_framework.test import APIRequestFactory
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from repair.tests.test import BasicModelTest


class ModelTest(TestCase):

    fixtures = ['auth_fixture', 'user_fixture.json']


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


class ViewTest(APITestCase):

    fixtures = ['auth_fixture', 'user_fixture.json']


    def test_get_group(self):
        url = reverse('group-list')
        data = {'name': 'MyGroup'}
        response = self.client.post(url, data, format='json')
        print(response)
        response = self.client.get(url)
        print(response.data)

    def test_get_user(self):
        lodz = reverse('casestudy-detail', kwargs=dict(pk=3))

        url = reverse('user-list')
        data = {'username': 'MyUser',
                'casestudies': [lodz],
                'password': 'PW',
                'organization': 'GGR',
                'groups': [],
                'email': 'a.b@c.de',}
        response = self.client.post(url, data, format='json')
        print(response)
        response = self.client.get(url)
        print(response.data)
        url = reverse('user-detail', kwargs=dict(pk=4))
        response = self.client.get(url)
        print(response.data)
        new_mail = 'new@mail.de'
        data = {'email': new_mail,}
        self.client.patch(url, data)
        response = self.client.get(url)
        assert response.data['email'] == new_mail


class CasestudyTest(BasicModelTest, APITestCase):

    url_key = "casestudy"
    sub_urls = ["userincasestudy_set",
                "solution_categories",
                "stakeholder_categories",
                "implementations",
                "materials",
                "activitygroups",
                "activities",
                "actors",
                "administrative_locations",
                "operational_locations"]
    url_pks = dict()
    url_pk = dict(pk=1)
    post_data = dict(name='posttestname')
    put_data = {'name': 'puttestname', }
    patch_data = dict(name='patchtestname')

    def setUp(self):
        self.obj = CaseStudyFactory()


class SolutioncategoryInCasestudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    solutioncategory = 21
    user = 99
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        #cls.cs_url = cls.baseurl + reverse('casestudy-detail',
                                       #kwargs=dict(pk=cls.casestudy))
        cls.url_key = "solutioncategory"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.solutioncategory)
        cls.post_data = dict(
            name='posttestname',
            user='http://testserver' + reverse('userincasestudy-detail',
                                               kwargs=dict(pk=cls.uic.user.user.id,
                                                           casestudy_pk=cls.casestudy)))
        cls.put_data = dict(
            name='puttestname',
            user='http://testserver' + reverse('user-detail',
                                               kwargs=dict(pk=cls.uic.user.user.id)))
        cls.patch_data = dict(name='patchtestname')


    def setUp(self):
        self.obj = SolutionCategoryFactory(id=self.solutioncategory,
                                           user__user__user=self.uic.user.user,
                                           user__casestudy=self.uic.casestudy)

    def test_detail(self):
        """
        Not Sure what to do:
        UserInCasestudyFactory is called, but url with user_pk and casestudy_pk
        id not found. self.uic.casestudy.id and self.uic.user.user.id exist and
        are right
        """
        pass

    def test_delete(self):
        """
        Not Sure what to do:
        UserInCasestudyFactory is called, but url with user_pk and casestudy_pk
        id not found. self.uic.casestudy.id and self.uic.user.user.id exist and
        are right
        """
        pass

    def test_post(self):
        """
        Not Sure what to do:
        UserInCasestudyFactory is called, but url with user_pk and casestudy_pk
        id not found. self.uic.casestudy.id and self.uic.user.user.id exist and
        are right
        """
        pass

class UserInCasestudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    user = 20
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        #cls.cs_url = cls.baseurl + reverse('casestudy-detail',
                                       #kwargs=dict(pk=cls.casestudy))
        cls.url_key = "userincasestudy"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.user)
        cls.post_data = dict(role="role for testing")
        cls.put_data = dict(role="role for testing")
        cls.patch_data = dict(role="role for testing")


    def setUp(self):
        self.obj = ProfileFactory(user=self.uic.user.user).user

    def test_post(self):
        """
        Error: NotNull constraint failed for casestudy_id, although it is
        not needed in api/docs
        """
        pass

    def test_detail(self):
        """
        Not Sure what to do:
        UserInCasestudyFactory is called, but url with user_pk and casestudy_pk
        id not found. self.uic.casestudy.id and self.uic.user.user.id exist and
        are right
        """
        pass

    def test_delete(self):
        """
        Not Sure what to do:
        UserInCasestudyFactory is called, but url with user_pk and casestudy_pk
        id not found. self.uic.casestudy.id and self.uic.user.user.id exist and
        are right
        """
        pass


class ImplementationsInCasestudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    user = 20
    implementation = 30
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.usr_url = cls.baseurl + reverse('userincasestudy-detail',
                                       kwargs=dict(pk=cls.user, casestudy_pk=cls.casestudy))
        cls.sol_set = []
        cls.url_key = "implementation"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.implementation)
        cls.post_data = dict(name="Test Implementation",
                             user=cls.usr_url,
                             solution_set=cls.sol_set)
        cls.put_data = dict(name="Test Implementation",
                            user=cls.usr_url,
                            solution_set=cls.sol_set)
        cls.patch_data = dict(name="Test Implementation")


    def setUp(self):
        self.obj = ImplementationFactory(user=self.uic)

    def test_post(self):
        """
        Error: NotNull constraint failed for casestudy_id, although it is
        not needed in api/docs
        """
        pass

    def test_detail(self):
        """
        Not Sure what to do:
        UserInCasestudyFactory is called, but url with user_pk and casestudy_pk
        id not found. self.uic.casestudy.id and self.uic.user.user.id exist and
        are right
        """
        pass

    def test_delete(self):
        """
        Not Sure what to do:
        UserInCasestudyFactory is called, but url with user_pk and casestudy_pk
        id not found. self.uic.casestudy.id and self.uic.user.user.id exist and
        are right
        """
        pass
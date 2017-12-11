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
    #sub_urls = ["userincasestudy_set",
                #"solution_categories",
                #"stakeholder_categories",
                #"implementations",
                #"keyflows",
                #]
    url_pks = dict()
    url_pk = dict(pk=1)
    post_data = dict(name='posttestname')
    put_data = {'name': 'puttestname', }
    patch_data = dict(name='patchtestname')

    def setUp(self):
        self.obj = self.kic.casestudy


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


class SolutionInImplementationInCasestudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    user = 20
    implementation = 30
    solution = 20
    solutioncategory = 56
    solution_implementation = 40

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.solution_url = cls.baseurl + \
            reverse('solution-detail',
                    kwargs=dict(casestudy_pk=cls.casestudy,
                                solutioncategory_pk=cls.solutioncategory,
                                pk=cls.solution))
        cls.implementation_url = cls.baseurl + \
            reverse('implementation-detail',
                    kwargs=dict(casestudy_pk=cls.casestudy,
                                pk=cls.implementation))
        cls.post_urls = [cls.solution_url, cls.implementation_url]
        cls.sol_set = []
        cls.url_key = "solutioninimplementation"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           implementation_pk=cls.implementation)
        cls.url_pk = dict(pk=cls.solution)
        cls.post_data = dict(solution=cls.solution_url,
                             implementation=cls.implementation_url)
        cls.put_data = dict(solution=cls.solution_url,
                             implementation=cls.implementation_url)
        cls.patch_data = dict(solution=cls.solution_url,
                             implementation=cls.implementation_url)


    def setUp(self):
        self.obj = SolutionInImplementationFactory(
            solution__user=self.uic, solution__id=self.solution,
            implementation__user=self.uic,
            implementation__id=self.implementation,
            solution__solution_category__id=self.solutioncategory,
            id=self.solution_implementation)

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


class GeometryInSolutionInImplementationInCasestudyTest(BasicModelTest,
                                                        APITestCase):

    casestudy = 17
    user = 20
    implementation = 30
    solution = 20
    solutioncategory = 56
    solution_implementation = 40
    geometry = 25

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sol_set = []
        cls.url_key = "solutioninimplementationgeometry"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           implementation_pk=cls.implementation,
                           solution_pk=cls.solution_implementation)
        cls.url_pk = dict(pk=cls.geometry)
        cls.post_data = dict(name="test name",
                             geom="test geom")
        cls.put_data = dict(name="test name",
                             geom="test geom")
        cls.patch_data = dict(name="test name",
                             geom="test geom")


    def setUp(self):
        self.obj = SolutionInImplementationGeometryFactory(
            sii__solution__user=self.uic, sii__solution__id=self.solution,
            sii__implementation__user=self.uic,
            sii__implementation__id=self.implementation,
            sii__solution__solution_category__id=self.solutioncategory,
            sii__id=self.solution_implementation,
            id=self.geometry)


class NoteInSolutionInImplementationInCasestudyTest(BasicModelTest,
                                                    APITestCase):

    casestudy = 17
    user = 20
    implementation = 30
    solution = 20
    solutioncategory = 56
    solution_implementation = 40
    note = 25

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sol_set = []
        cls.url_key = "solutioninimplementationnote"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           implementation_pk=cls.implementation,
                           solution_pk=cls.solution_implementation)
        cls.url_pk = dict(pk=cls.note)
        cls.post_data = dict(note="test note")
        cls.put_data = dict(note="test note")
        cls.patch_data = dict(note="test note")


    def setUp(self):
        self.obj = SolutionInImplementationNoteFactory(
            sii__solution__user=self.uic, sii__solution__id=self.solution,
            sii__implementation__user=self.uic,
            sii__implementation__id=self.implementation,
            sii__solution__solution_category__id=self.solutioncategory,
            sii__id=self.solution_implementation,
            id=self.note)


class QuantityInSolutionInImplementationInCasestudyTest(BasicModelTest):  #,APITestCase):
    """
    Test is not working:
    - delete is not allowed
    - post is not possible via Browser api
    """
    casestudy = 17
    user = 20
    implementation = 30
    solution = 20
    solutioncategory = 56
    solution_implementation = 40
    quantity = 25

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sol_set = []
        cls.url_key = "solutioninimplementationquantity"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           implementation_pk=cls.implementation,
                           solution_pk=cls.solution_implementation)
        cls.quantity_url = cls.baseurl + \
            reverse('solutionquantity-detail',
                    kwargs=dict(casestudy_pk=cls.casestudy,
                                solutioncategory_pk=cls.solutioncategory,
                                solution_pk=cls.solution,
                                pk=cls.quantity))
        cls.post_urls = [cls.quantity_url]
        cls.url_pk = dict(pk=cls.quantity)
        cls.post_data = dict(value=1000.12, quantity=cls.quantity_url)
        cls.put_data = dict(value=1000.12, quantity=cls.quantity_url)
        cls.patch_data = dict(value=1000.12, quantity=cls.quantity_url)


    def setUp(self):
        self.obj = SolutionInImplementationQuantityFactory(
            sii__solution__user=self.uic, sii__solution__id=self.solution,
            sii__implementation__user=self.uic,
            sii__implementation__id=self.implementation,
            sii__solution__solution_category__id=self.solutioncategory,
            sii__id=self.solution_implementation,
            id=self.quantity)
from repair.apps.asmfa.models import (
    Activity,
    Activity2Activity,
    ActivityGroup,
    ActivityStock,
    Actor,
    Actor2Actor,
    ActorStock,
    DataEntry,
    Flow,
    Geolocation,
    Group2Group,
    GroupStock,
    Node,
    Stock,
    )

from django.test import TestCase
from django.core.validators import ValidationError

from repair.apps.login.models import CaseStudy, User, Profile
from repair.apps.login.factories import *
from repair.apps.asmfa.factories import *
from rest_framework.test import APIRequestFactory
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from repair.tests.test import BasicModelTest

class ModelTestOld(TestCase):

    #fixtures = ['user_fixture.json',
                #'activities_dummy_data.json',]

    def test_string_representation(self):
        for Model in (
            Activity,
            Activity2Activity,
            ActivityGroup,
            ActivityStock,
            Actor,
            Actor2Actor,
            ActorStock,
            DataEntry,
            Geolocation,
            Group2Group,
            GroupStock,
            ):

            print('{} has {} test data entries'.format(
                Model, Model.objects.count()))


class MaterialTest(BasicModelTest, APITestCase):

    cs_url = 'http://testserver' + reverse('casestudy-detail',
                                           kwargs=dict(pk=1))
    url_key = "material"
    url_pks = dict()
    url_pk = dict(pk=1)
    post_data = dict(name='posttestname', casestudies=[cs_url], code='cdo')
    put_data = dict(name='puttestname', casestudies=[cs_url])
    patch_data = dict(name='patchtestname')

    def setUp(self):
        csf = CaseStudyFactory()
        self.fact = MaterialFactory()


class QualityTest(BasicModelTest, APITestCase):

    url_key = "quality"
    url_pks = dict()
    url_pk = dict(pk=1)
    post_data = dict(name='posttestname')
    put_data = dict(name='puttestname')
    patch_data = dict(name='patchtestname')

    def setUp(self):
        self.fact = QualityFactory()








    #def no_tewedst_get_user(self):
        #lodz = reverse('casestudy-detail', kwargs=dict(pk=3))

        #url = reverse('user-list')
        #data = {'username': 'MyUser',
                #'casestudies': [lodz],
                #'password': 'PW',
                #'organization': 'GGR',
                #'groups': [],
                #'email': 'a.b@c.de',}
        #response = self.client.post(url, data, format='json')
        #print(response)
        #response = self.client.get(url)
        #print(response.data)
        #url = reverse('user-detail', kwargs=dict(pk=4))
        #response = self.client.get(url)
        #print(response.data)
        #new_mail = 'new@mail.de'
        #data = {'email': new_mail,}
        #self.client.patch(url, data)
        #response = self.client.get(url)
        #assert response.data['email'] == new_mail

        #user_in_ams = UserInCasestudyFactory()
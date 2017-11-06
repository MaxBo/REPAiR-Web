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
from rest_framework.test import APIRequestFactory
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status

class ModelTest(TestCase):

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

class ViewTest(APITestCase):

    #fixtures = ['activities_dummy_data.json']


    def test_get_casestudies_list(self):
        url = reverse('casestudy-list')
        response = self.client.get(url)
        assert response.status_code == 200

    def test_get_casestudy_detail(self):
        cs = CaseStudyFactory()
        old_name = cs.name
        new_name = "changed name"
        data = {'name': new_name,}
        url = reverse('casestudy-detail', kwargs=dict(pk=1))
        # test get
        response = self.client.get(url)
        assert response.data['id'] == 1
        # check status code for put
        response = self.client.put(url, data=data, format='json')
        assert response.status_code == 200
        # check if name has changed
        response = self.client.get(url)
        assert response.data['name'] == new_name
        # check status code for patch
        data = {'name': old_name,}
        response = self.client.patch(url, data=data, format='json')
        assert response.status_code == 200
        # check if name has changed
        response = self.client.get(url)
        assert response.data['name'] == old_name

    def test_delete(self):
        cs = CaseStudyFactory()
        url = reverse('casestudy-detail', kwargs=dict(pk=1))
        response = self.client.get(url)
        assert response.status_code == 200
        response = self.client.delete(url)
        response = self.client.get(url)
        assert response.status_code == 404

    def test_post(self):
        data = {'name': "test casestudy",}
        url = reverse('casestudy-list')
        # post
        response = self.client.post(url, data)
        assert response.data['name'] == data['name']
        # get
        new_id = response.data['id']
        url = reverse('casestudy-detail', kwargs=dict(pk=new_id))
        response = self.client.get(url)
        assert response.status_code == 200






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
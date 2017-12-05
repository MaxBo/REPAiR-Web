import json
from unittest import skipIf

from django.core.validators import ValidationError
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIRequestFactory
from rest_framework.test import APITestCase

from repair.apps.login.models import CaseStudy, User, Profile
from repair.apps.login.factories import *
from repair.apps.asmfa.factories import *

class BasicModelTest(object):
    baseurl = 'http://testserver'
    url_key = ""
    sub_urls = []
    url_pks = dict()
    url_pk = dict()
    post_urls = []
    post_data = dict()
    put_data = dict()
    patch_data = dict()
    casestudy = None
    user = -1

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uic = UserInCasestudyFactory(user__user__id=cls.user,
                                         user__user__username='Anonymus User',
                                         casestudy__id = cls.casestudy)

    @classmethod
    def tearDownClass(cls):
        user = cls.uic.user.user
        cs = cls.uic.casestudy
        user.delete()
        cs.delete()
        del cls.uic
        super().tearDownClass()

    def test_list(self):
        url = reverse(self.url_key + '-list', kwargs=self.url_pks)
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_detail(self):
        kwargs={**self.url_pks, 'pk': self.obj.pk,}
        url = reverse(self.url_key + '-detail', kwargs=kwargs)
        # test get
        response = self.client.get(url)
        assert response.data['id'] == self.obj.pk
        # check status code for put
        response = self.client.put(url, data=self.put_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        # check if name has changed
        response = self.client.get(url)
        for key in self.put_data:
            assert response.data[key] == self.put_data[key]
            #self.assertJSONEqual(response.data[key], self.put_data[key])            
        # check status code for patch
        response = self.client.patch(url, data=self.patch_data, format='json')
        assert response.status_code == status.HTTP_200_OK
        # check if name has changed
        response = self.client.get(url)
        for key in self.patch_data:
            assert response.data[key] == self.patch_data[key]

    def test_delete(self):
        kwargs =  {**self.url_pks, 'pk': self.obj.pk, }
        url = reverse(self.url_key + '-detail', kwargs=kwargs)
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        response = self.client.delete(url)
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_post(self):
        url = reverse(self.url_key +'-list', kwargs=self.url_pks)
        # post
        response = self.client.post(url, self.post_data)
        for key in self.post_data:
            assert response.data[key] == self.post_data[key]
        # get
        new_id = response.data['id']
        url = reverse(self.url_key + '-detail', kwargs={**self.url_pks,
                                                        'pk': new_id})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_urls(self):
        url = reverse(self.url_key + '-detail', kwargs={**self.url_pks,
                                                            'pk': self.obj.pk,})
        response = self.client.get(url)
        for key in self.sub_urls:
            key_response = self.client.get(response.data[key])
            assert key_response.status_code == status.HTTP_200_OK

    def test_post_url_exist(self):
        kwargs={**self.url_pks, 'pk': self.obj.pk,}
        url = reverse(self.url_key + '-detail', kwargs=kwargs)
        response = self.client.get(url)
        for url in self.post_urls:
            response = self.client.get(url)
            assert response.status_code == status.HTTP_200_OK


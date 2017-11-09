from django.test import TestCase
from django.core.validators import ValidationError

from repair.apps.login.models import CaseStudy, User, Profile
from repair.apps.login.factories import *
from repair.apps.asmfa.factories import *
from rest_framework.test import APIRequestFactory
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
import json
from unittest import skipIf

class ModelTest(object):
    url_key = ""
    url_pks = dict()
    url_pk = dict()
    post_data = dict()
    put_data = dict()
    patch_data = dict()

    def test_list(self):
        url = reverse(self.url_key + '-list', kwargs=self.url_pks)
        response = self.client.get(url)
        assert response.status_code == 200

    def test_detail(self):
        url = reverse(self.url_key + '-detail', kwargs={ **self.url_pks,
                                                         'pk': self.fact.pk,})
        # test get
        response = self.client.get(url)
        assert response.data['id'] == self.fact.pk
        # check status code for put
        response = self.client.put(url, data=self.put_data, format='json')
        assert response.status_code == 200
        # check if name has changed
        response = self.client.get(url)
        for key in self.put_data:
            assert response.data[key] == self.put_data[key]
        # check status code for patch
        response = self.client.patch(url, data=self.patch_data, format='json')
        assert response.status_code == 200
        # check if name has changed
        response = self.client.get(url)
        for key in self.patch_data:
            assert response.data[key] == self.patch_data[key]

    def test_delete(self):
        url = reverse(self.url_key + '-detail', kwargs={**self.url_pks,
                                                        'pk': self.fact.pk, })
        response = self.client.get(url)
        assert response.status_code == 200
        response = self.client.delete(url)
        response = self.client.get(url)
        assert response.status_code == 404

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
        assert response.status_code == 200
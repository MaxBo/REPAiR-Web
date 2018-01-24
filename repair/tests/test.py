from abc import ABCMeta
import json
from unittest import skipIf

from django.core.validators import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.http import HttpRequest

from rest_framework_gis.fields import GeoJsonDict
from django.utils.encoding import force_text

from rest_framework import status
from test_plus import APITestCase

from repair.apps.login.models import CaseStudy, User, Profile
from repair.apps.login.factories import UserInCasestudyFactory
from repair.apps.asmfa.factories import KeyflowInCasestudyFactory
from django.contrib.auth.models import Permission


class CompareAbsURIMixin:
    """
    Mixin thats provide a method
    to compare lists of relative with absolute url
    """
    @property
    def build_absolute_uri(self):
        """return the absolute_uri-method"""
        request = HttpRequest()
        request.META = self.client._base_environ()
        return request.build_absolute_uri

    def assertURLEqual(self, url1, url2, msg=None):
        """Assert that two urls are equal, if they were absolute urls"""
        absurl1 = self.build_absolute_uri(url1)
        absurl2 = self.build_absolute_uri(url2)
        self.assertEqual(absurl1, absurl2, msg)

    def assertURLsEqual(self, urllist1, urllist2, msg=None):
        """
        Assert that two lists of urls are equal, if they were absolute urls
        the order does not matter
        """
        absurlset1 = {self.build_absolute_uri(url) for url in urllist1}
        absurlset2 = {self.build_absolute_uri(url) for url in urllist2}
        self.assertSetEqual(absurlset1, absurlset2, msg)


class LoginTestCase:

    casestudy = None
    keyflow = None
    userincasestudy = 26
    user = -1

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uic = UserInCasestudyFactory(id=cls.userincasestudy,
                                         user__user__id=cls.user,
                                         user__user__username='Anonymus User',
                                         casestudy__id = cls.casestudy)
        cls.kic = KeyflowInCasestudyFactory(id=cls.keyflow,
                                            casestudy=cls.uic.casestudy)

    def setUp(self):
        self.client.force_login(user=self.uic.user.user)
        super().setUp()

    def tearDown(self):
        self.client.logout()
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        user = cls.uic.user.user
        cs = cls.uic.casestudy
        user.delete()
        cs.delete()
        del cls.uic
        super().tearDownClass()


class BasicModelReadTest(LoginTestCase, CompareAbsURIMixin):
    baseurl = 'http://testserver'
    url_key = ""
    sub_urls = []
    url_pks = dict()
    url_pk = dict()
    put_data = dict()
    patch_data = dict()
    do_not_check = []

    def test_list(self):
        """Test that the list view can be returned successfully"""
        self.get_check_200(self.url_key + '-list', **self.url_pks)

    def test_detail(self):
        """Test get, put, patch methods for the detail-view"""
        url = self.url_key + '-detail'
        kwargs={**self.url_pks, 'pk': self.obj.pk,}
        formatjson = dict(format='json')

        # test get
        response = self.get_check_200(url, **kwargs)
        assert response.data['id'] == self.obj.pk

        # check status code for put
        response = self.put(url, **kwargs,
                            data=self.put_data,
                            extra=formatjson)
        self.response_200()
        assert response.status_code == status.HTTP_200_OK
        # check if values have changed
        response = self.get_check_200(url, **kwargs)
        for key in self.put_data:
            if key not in response.data.keys() or key in self.do_not_check:
                continue
            response_value = response.data[key]
            expected = self.put_data[key]
            self.assert_response_equals_expected(response_value, expected)

        # check status code for patch
        response = self.patch(url, **kwargs,
                              data=self.patch_data, extra=formatjson)
        self.response_200()

        # check if name has changed
        response = self.get_check_200(url, **kwargs)
        for key in self.patch_data:
            if key not in response.data.keys():
                continue
            response_value = response.data[key]
            expected = self.patch_data[key]
            self.assert_response_equals_expected(response_value, expected)

    def assert_response_equals_expected(self, response_value, expected):
        """
        Assert that response_value equals expected
        If response_value is a GeoJson, then compare the texts
        """
        if isinstance(response_value, GeoJsonDict):
            self.assertJSONEqual(force_text(response_value), expected)
        else:
            self.assertEqual(force_text(response_value), force_text(expected))

    def test_get_urls(self):
        """get all sub-elements of a list of urls"""
        url = self.url_key + '-detail'
        response = self.get_check_200(url, pk=self.obj.pk, **self.url_pks)
        for key in self.sub_urls:
            key_response = self.get_check_200(response.data[key])


class BasicModelTest(BasicModelReadTest):
    post_urls = []
    post_data = dict()

    def test_delete(self):
        """Test delete method for the detail-view"""
        kwargs =  {**self.url_pks, 'pk': self.obj.pk, }
        url = self.url_key + '-detail'
        response = self.get_check_200(url, **kwargs)

        response = self.delete(url, **kwargs)
        self.response_204()

        # it should be deleted and raise 404
        response = self.get(url, **kwargs)
        self.response_404()

    def test_post(self):
        """Test post method for the detail-view"""
        url = self.url_key +'-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data)
        self.response_201()
        for key in self.post_data:
            if key not in response.data.keys() or key in self.do_not_check:
                continue
            response_value = response.data[key]
            expected = self.post_data[key]
            self.assert_response_equals_expected(response_value, expected)

        # get the created object
        new_id = response.data['id']
        url = self.url_key + '-detail'
        self.get_check_200(url, pk=new_id, **self.url_pks)

    def test_post_url_exist(self):
        """post all sub-elements of a list of urls"""
        url = self.url_key + '-detail'
        response = self.get_check_200(url, pk=self.obj.pk, **self.url_pks)
        for url in self.post_urls:
            response = self.get_check_200(url)


class BasicModelPermissionTest(BasicModelTest):
    permissions = Permission.objects.all()

    def tearDown(self):
        self.uic.user.user.user_permissions.set(list(self.permissions))
        super().tearDown()

    def test_post_permission(self):
        """
        Test if user can post without permission
        """
        self.uic.user.user.user_permissions.clear()
        url = self.url_key +'-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data)
        self.response_403()

    def test_delete_permission(self):
        """
        Test if user can delete without permission
        """
        self.uic.user.user.user_permissions.clear()
        kwargs =  {**self.url_pks, 'pk': self.obj.pk, }
        url = self.url_key + '-detail'
        response = self.get_check_200(url, **kwargs)
        response = self.delete(url, **kwargs)
        self.response_403()

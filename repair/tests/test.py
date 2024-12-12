from django.http import HttpRequest

from rest_framework_gis.fields import GeoJsonDict
from django.utils.encoding import force_text

from rest_framework import status
from django.urls import reverse

from repair.apps.login.factories import UserInCasestudyFactory, CaseStudyFactory
from repair.apps.asmfa.factories import KeyflowInCasestudyFactory
from django.contrib.auth.models import Permission
from repair.apps.login.models import User
from django.test.client import Client as FormClient


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
    user = 99
    permissions = Permission.objects.all()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.casestudy_obj = CaseStudyFactory(id=cls.casestudy)
        cls.uic = UserInCasestudyFactory(id=cls.userincasestudy,
                                         user__user__id=cls.user,
                                         user__user__username='Anonymus User',
                                         casestudy=cls.casestudy_obj)
        cls.kic_obj = KeyflowInCasestudyFactory(id=cls.keyflow,
                                                casestudy=cls.casestudy_obj)

    def setUp(self):
        self.client.force_login(user=self.uic.user.user)
        self.uic.user.user.user_permissions.set(list(self.permissions))
        super().setUp()

    def tearDown(self):
        self.client.logout()
        self.uic.user.user.user_permissions.set(list(self.permissions))
        super().tearDown()

    @classmethod
    def tearDownClass(cls):
        user = cls.uic.user.user
        user.delete()
        cls.kic_obj.delete()
        cls.uic.delete()
        cls.casestudy_obj.delete()
        if getattr(cls, 'obj', None):
            try:
                cls.obj.delete()
            except:
                pass
        super().tearDownClass()


class BasicModelReadTest(LoginTestCase, CompareAbsURIMixin):
    baseurl = 'http://testserver'
    url_key = ""
    sub_urls = []
    url_pks = dict()
    url_pk = dict()
    do_not_check = []

    def test_list(self):
        """Test that the list view can be returned successfully"""
        self.get_check_200(self.url_key + '-list', **self.url_pks)

    def test_detail(self):
        """Test get, put, patch methods for the detail-view"""
        url = self.url_key + '-detail'
        kwargs = {**self.url_pks, 'pk': self.obj.pk}

        # test get
        response = self.get_check_200(url, **kwargs)
        assert response.data['id'] == self.obj.pk

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
    put_data = dict()
    patch_data = dict()

    def test_delete(self):
        """Test delete method for the detail-view"""
        kwargs = {**self.url_pks, 'pk': self.obj.pk, }
        url = self.url_key + '-detail'
        response = self.get_check_200(url, **kwargs)

        response = self.delete(url, **kwargs)
        self.response_204()

        # it should be deleted and raise 404
        response = self.get(url, **kwargs)
        self.response_404()

    def test_post(self):
        """Test post method for the detail-view"""
        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                             extra={'format': 'json'})
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

    def test_put_patch(self):
        """Test get, put, patch methods for the detail-view"""
        url = self.url_key + '-detail'
        kwargs = {**self.url_pks, 'pk': self.obj.pk, }
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
            if key not in response.data.keys() or key in self.do_not_check:
                continue
            response_value = response.data[key]
            expected = self.patch_data[key]
            self.assert_response_equals_expected(response_value, expected)


class BasicModelReadPermissionTest(BasicModelReadTest):
    def test_list_permission(self):
        self.uic.user.user.user_permissions.clear()
        response = self.get(self.url_key + '-list', **self.url_pks)
        self.response_403()

    def test_get_permission(self):
        self.uic.user.user.user_permissions.clear()
        url = self.url_key + '-detail'
        kwargs = {**self.url_pks, 'pk': self.obj.pk, }
        response = self.get(url, **kwargs)
        self.response_403()


class BasicModelWritePermissionTest(BasicModelTest):

    def test_post_permission(self):
        """
        Test if user can post without permission
        """
        self.uic.user.user.user_permissions.clear()
        url = self.url_key + '-list'
        # post
        response = self.post(url, **self.url_pks, data=self.post_data,
                             extra={'format': 'json'})
        self.response_403()

    def test_delete_permission(self):
        """
        Test if user can delete without permission
        """
        self.uic.user.user.user_permissions.clear()
        kwargs = {**self.url_pks, 'pk': self.obj.pk, }
        url = self.url_key + '-detail'
        response = self.delete(url, **kwargs)
        self.response_403()

    def test_put_permission(self):
        self.uic.user.user.user_permissions.clear()
        url = self.url_key + '-detail'
        kwargs = {**self.url_pks, 'pk': self.obj.pk, }
        formatjson = dict(format='json')
        response = self.put(url, **kwargs, data=self.put_data,
                            extra=formatjson)
        self.response_403()


class BasicModelPermissionTest(BasicModelReadPermissionTest,
                               BasicModelWritePermissionTest):
    """
    Test of read and write permissions
    """


class AdminAreaTest:
    """
    Test functions for the admin area
    """
    app = 'modelname'
    model = 'modelname'
    add_data = {}
    form_class = None
    model_class = None
    check_feature = None
    incomplete_data = None

    @classmethod
    def setUpClass(cls):
        """
        Create a user with admin rights.
        """
        super().setUpClass()
        cls.username = "test_admin"
        cls.password = User.objects.make_random_password()
        user, created = User.objects.get_or_create(username=cls.username)
        user.set_password(cls.password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        cls.admin_user = user
        cls.admin_client = FormClient()

    def as_admin(self, function):
        """
        Login to client before running 'function()'.
        """
        self.admin_client.login(username=self.username, password=self.password)
        result = function()
        self.admin_client.logout()
        return result

    def admin_add(self):
        """
        Add a model instance in the admin area.
        """
        change_url = reverse('admin:{}_{}_add'.format(self.app, self.model))
        keyflow = KeyflowInCasestudyFactory()
        self.add_management_form_data()
        response = self.admin_client.post(change_url, self.add_data)
        return response

    def add_management_form_data(self, form_data=None):
        if not form_data:
            form_data = {'wmslayer_set-TOTAL_FORMS': ['3'],
                         'wmslayer_set-INITIAL_FORMS': ['0'],
                         'wmsresourceincasestudy_set-TOTAL_FORMS': ['3'],
                         'wmsresourceincasestudy_set-INITIAL_FORMS': ['0']}
        self.add_data.update(form_data)


    def test_admin_add(self):
        """
        Test if User with admin rights can create a model.
        """
        old_objects = self.model_class.objects.all().count()
        response = self.as_admin(self.admin_add)
        new_objects = self.model_class.objects.all().count()
        # test if one more object exsists
        assert new_objects - old_objects == 1
        # check if the feature is present (for example name)
        if self.check_feature:
            assert self.model_class.objects.filter(
                name=self.add_data[self.check_feature][0]).exists()
        # test if an object is created although the data is incomplete
        if self.incomplete_data:
            old_objects = self.model_class.objects.all().count()
            response = self.as_admin(self.admin_add)
            new_objects = self.model_class.objects.all().count()
            assert new_objects - old_objects == 0

    def admin_read(self):
        """
        Access the admin area of a model.
        """
        read_url = reverse('admin:{}_{}_changelist'.format(self.app,
                                                           self.model))
        response = self.admin_client.get(read_url)
        return response

    def test_admin_read(self):
        """
        Check if an admin user can access the admin area of the model.
        """
        response = self.as_admin(self.admin_read)
        self.assertIs(response.status_code, 200)

    #def admin_delete(self):
        #"""
        #Delete a model in the admin area.
        #"""
        #response = self.as_admin(self.admin_add)
        #response = self.as_admin(self.admin_read)
        #delete_url = reverse('admin:{}_{}_history'.format(self.app, self.model))
        #self.admin_client

    #def test_admin_delete(self):
        #response = self.as_admin(self.admin_delete)
        #self.response_200(response)
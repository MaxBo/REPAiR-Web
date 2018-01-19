# -*- coding: utf-8 -*-

from django.urls import reverse
from test_plus import APITestCase
from repair.tests.test import BasicModelTest


from repair.apps.publications.factories import *
from repair.apps.login.factories import ProfileFactory, UserInCasestudyFactory


class PublicationInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 1
    casestudy2 = 21
    publication = 11
    pup_type = 'Handwriting'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cs_url = cls.baseurl + reverse('casestudy-detail',
                                   kwargs=dict(pk=cls.casestudy))

        cls.url_key = "publicationincasestudy"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.publication)

        cls.put_data = dict(title='new_put_title',
                             )
        cls.post_data = dict(title='new_title',
                             type=cls.pup_type)

        cls.patch_data = dict(title='patchtest_title')

    def setUp(self):
        super().setUp()
        self.obj = PublicationInCasestudyFactory(casestudy=self.uic.casestudy,
                                                 publication__id=self.publication,
                                                 publication__type__title=self.pup_type)

    def test_post_existing_publication(self):
        """Test post method for the detail-view"""
        # create a user with 2 casestudies
        user_id = 33
        casestudy1 = 11
        casestudy2 = 22
        user = ProfileFactory(user__id=user_id, user__username='User')
        uic1 = UserInCasestudyFactory(user=user,
                                      casestudy__id=casestudy1)
        uic2 = UserInCasestudyFactory(user=user,
                                      casestudy__id=casestudy2)


        url = self.url_key +'-list'
        # post
        post_data = dict(title='important reference for many casestudies',
                         type=self.pup_type)

        # add a publication for casestudy 1
        self.client.force_login(user=uic1.user.user)
        response = self.post(url, casestudy_pk=casestudy1,
                             data=self.post_data)
        new_id1 = response.data['id']
        self.response_201()
        for key in self.post_data:
            if key not in response.data.keys() or key in self.do_not_check:
                continue
            self.assertEqual(str(response.data[key]),
                             str(self.post_data[key]))
        self.client.logout()

        # add a publication for casestudy 2
        self.client.force_login(user=uic2.user.user)
        response = self.post(url, casestudy_pk=casestudy2,
                             data=self.post_data)
        new_id2 = response.data['id']
        self.response_201()
        for key in self.post_data:
            if key not in response.data.keys() or key in self.do_not_check:
                continue
            self.assertEqual(str(response.data[key]),
                             str(self.post_data[key]))
        self.client.logout()

        # get the created object for casestudy1
        self.client.force_login(user=uic1.user.user)
        url = self.url_key + '-detail'
        response = self.get_check_200(url, pk=new_id1, casestudy_pk=casestudy1)
        pub1 = response.data
        self.client.logout()

        # get the created object for casestudy2
        self.client.force_login(user=uic2.user.user)
        response = self.get_check_200(url, pk=new_id2, casestudy_pk=casestudy2)
        pub2 = response.data
        self.client.logout()

        # the publication should be the same
        self.assertEqual(pub1['publication_id'], pub2['publication_id'])

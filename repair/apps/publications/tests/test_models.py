# -*- coding: utf-8 -*-

from django.urls import reverse
from test_plus import APITestCase
from repair.tests.test import BasicModelTest

from repair.apps.publications.factories import PublicationInCasestudyFactory
from repair.apps.login.factories import ProfileFactory, UserInCasestudyFactory


class PublicationInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 1
    casestudy2 = 21
    publication = 11
    pup_type = 'Handwriting'
    user_id = 33
    casestudy1 = 11
    casestudy2 = 22

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
        self.obj = PublicationInCasestudyFactory(
            casestudy=self.uic.casestudy,
            publication__id=self.publication,
            publication__type__title=self.pup_type)

        # create a user with 2 casestudies
        self.user = ProfileFactory(user__id=self.user_id,
                                   user__username='User')
        self.uic1 = UserInCasestudyFactory(user=self.user,
                                           casestudy__id=self.casestudy1)
        self.uic2 = UserInCasestudyFactory(user=self.user,
                                           casestudy__id=self.casestudy2)

    def test_post_existing_publication(self):
        """Test post method for the detail-view"""
        url = self.url_key + '-list'
        # post
        self.post_data = dict(title='important reference for many casestudies',
                              type=self.pup_type)

        # add a publication for casestudy 1
        self.client.force_login(user=self.uic1.user.user)
        response = self.post(url, casestudy_pk=self.casestudy1,
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
        self.client.force_login(user=self.uic2.user.user)
        response = self.post(url, casestudy_pk=self.casestudy2,
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
        self.client.force_login(user=self.uic1.user.user)
        url = self.url_key + '-detail'
        response = self.get_check_200(url, pk=new_id1,
                                      casestudy_pk=self.casestudy1)
        pub1 = response.data
        self.client.logout()

        # get the created object for casestudy2
        self.client.force_login(user=self.uic2.user.user)
        response = self.get_check_200(url, pk=new_id2,
                                      casestudy_pk=self.casestudy2)
        pub2 = response.data
        self.client.logout()

        # the publication should be the same
        self.assertEqual(pub1['publication_id'], pub2['publication_id'])

    def test_upload_bibtex(self):
        """Test upload of a bibtex reference"""
        bibtex = """
@article{McDowall2012,
author = {McDowall, Will and Geng, Yong and Huang, Beijia and Bartekov{\'{a}}, Eva and Bleischwitz, Raimund and T{\"{u}}rkeli, Serdar and Kemp, Ren{\'{e}} and Dom{\'{e}}nech, Teresa},
doi = {10.1111/jiec.12345},
file = {:Users/rusnesileryte/Library/Application Support/Mendeley Desktop/Downloaded/McDowall et al. - 2017 - Circular Economy Policies in China and Europe.pdf:pdf},
issn = {10881980},
journal = {Journal of Industrial Ecology},
keywords = {China,European Union,circular economy,environmental governance,indicator,industrial ecology},
month = {jun},
number = {3},
pages = {651--661},
title = {{Circular Economy Policies in China and Europe}},
url = {http://doi.wiley.com/10.1111/jiec.12345},
volume = {21},
year = {2012}
}
        """
        # existing publications of the user
        self.client.force_login(user=self.uic1.user.user)
        self.client.session['casestudy'] = self.casestudy
        url = self.url_key + '-list'
        response = self.get_check_200(url, casestudy_pk=self.casestudy1)

        url_post = '/admin/publications_bootstrap/publication/import_bibtex/'
        response = self.post(url_post, data={'bibliography': bibtex},
                             follow=True)
        # the response is redirected
        self.response_200(response)
        content = str(response.content)
        success_tag = '<li class="success">'
        success_index = content.find(success_tag)
        assert success_index != -1
        msg = 'Successfully added 1 publication (0 error(s) occurred)'
        assert content[(success_index + len(success_tag)):].startswith(msg)

        bibtex = """

@article{Wandl2012,
author = {Wandl},
year = 2012,
title = {Test1}
}
@article{Wandl2013,
author = {Wandl},
year = 2013,
title = {Test2}
}
        """
        self.client.session['casestudy'] = self.casestudy
        response = self.post(url_post, data={'bibliography': bibtex},
                             follow=True)
        # the response is redirected
        self.response_200(response)
        content = str(response.content)
        success_tag = '<li class="success">'
        success_index = content.find(success_tag)
        assert success_index != -1
        msg = 'Successfully added 2 publications (0 skipped due to errors)'
        assert content[(success_index + len(success_tag)):].startswith(msg)

        self.client.logout()

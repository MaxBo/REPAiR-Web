# -*- coding: utf-8 -*-

from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status
from repair.tests.test import BasicModelTest, LoginTestCase

from repair.apps.asmfa.factories import (ActivityFactory,
                                         ActivityGroupFactory,
                                         ActorFactory)


class TestActor(LoginTestCase, APITestCase):

    def test_actor_website(self):
        """Test updating a website for an actor"""
        # create actor and casestudy
        actor = ActorFactory()
        keyflow = actor.activity.activitygroup.keyflow

        # define the urls
        url_actor = reverse('actor-detail',
                            kwargs={'casestudy_pk': keyflow.casestudy_id,
                                    'keyflow_pk': keyflow.pk,
                                    'pk': actor.pk,})

        data_to_test = [
            {'website' : 'website.without.http.de'},
            {'website' : 'https://website.without.http.de'},
        ]

        for data in data_to_test:
            response = self.client.patch(url_actor, data)
            assert response.status_code == status.HTTP_200_OK

        data = {'website' : 'website.without.http+.de'}
        response = self.client.patch(url_actor, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class ActorInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    keyflow = 23
    actor = 5
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cs_url = cls.baseurl + reverse('casestudy-detail',
                                           kwargs=dict(pk=cls.casestudy))
        cls.url_key = "actor"
        cls.url_pks = dict(casestudy_pk=cls.casestudy, keyflow_pk=cls.keyflow)
        cls.url_pk = dict(pk=cls.actor)
        cls.post_data = dict(name='posttestname', year=2017, turnover='1000.00',
                             employees=2, activity=1, BvDid='141234')
        cls.put_data = dict(name='posttestname', year=2017, turnover='1000.00',
                            employees=2, activity=1, BvDid='141234')
        cls.patch_data = dict(name='patchtestname')


    def setUp(self):
        super().setUp()
        self.obj = ActorFactory(activity__activitygroup__keyflow=self.kic)


class ActivityInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    activity = 5
    activitygroup = 90
    keyflow = 23
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ag_url = cls.baseurl + reverse('activitygroup-detail',
                                           kwargs=dict(pk=cls.activity,
                                                       casestudy_pk=cls.casestudy,
                                                       keyflow_pk=cls.keyflow))
        cls.url_key = "activity"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflow)
        cls.url_pk = dict(pk=cls.activity)
        cls.post_data = dict(nace="Test Nace",
                             name="Test Name",
                             activitygroup=cls.activitygroup)
        cls.put_data = dict(nace="Test Nace",
                             name="Test Name",
                             activitygroup=cls.activitygroup)
        cls.patch_data = dict(name='Test Name')


    def setUp(self):
        super().setUp()
        self.obj = ActivityFactory(
            activitygroup__keyflow__casestudy=self.uic.casestudy,
            activitygroup__keyflow=self.kic,
            activitygroup__id=self.activitygroup)


class ActivitygroupInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    activitygroup = 90
    keyflow = 23
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "activitygroup"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflow)
        cls.url_pk = dict(pk=cls.activitygroup)
        cls.post_data = dict(code="P1", name='Test Code')
        cls.put_data = dict(code="P1", name='Test Code')
        cls.patch_data = dict(name='P1')


    def setUp(self):
        super().setUp()
        self.obj = ActivityGroupFactory(keyflow=self.kic)


class ActivityInActivitygroupInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    activity = 5
    activitygroup = 90
    keyflow = 23
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ag_url = cls.baseurl + reverse('activitygroup-detail',
                                           kwargs=dict(pk=cls.activity,
                                                       casestudy_pk=cls.casestudy,
                                                       keyflow_pk=cls.keyflow))
        cls.url_key = "activity"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflow,
                           activitygroup_pk=cls.activitygroup)
        cls.url_pk = dict(pk=cls.activity)
        cls.post_data = dict(nace="Test Nace",
                             name="Test Name",
                             activitygroup=cls.activitygroup)
        cls.put_data = dict(nace="Test Nace",
                             name="Test Name",
                             activitygroup=cls.activitygroup)
        cls.patch_data = dict(name='Test Name')


    def setUp(self):
        super().setUp()
        self.obj = ActivityFactory(
            activitygroup__keyflow=self.kic,
            activitygroup__keyflow__casestudy=self.uic.casestudy,
            activitygroup__id=self.activitygroup)

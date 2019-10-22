# -*- coding: utf-8 -*-

from django.urls import reverse
from django.core.exceptions import ValidationError
from test_plus import APITestCase
from rest_framework import status
from repair.tests.test import BasicModelPermissionTest, LoginTestCase

from repair.apps.asmfa.factories import (ActivityFactory,
                                         ActivityGroupFactory,
                                         ActorFactory,
                                         ReasonFactory,
                                         )
from repair.apps.asmfa.models import ActivityGroup, Activity


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
                                    'pk': actor.pk, })

        data_to_test = [
            {'website': 'website.without.http.de'},
            {'website': 'https://website.without.http.de'},
        ]

        for data in data_to_test:
            response = self.client.patch(url_actor, data)
            assert response.status_code == status.HTTP_200_OK

        data = {'website': 'website.without.http+.de'}
        response = self.client.patch(url_actor, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class ActorInCaseStudyTest(BasicModelPermissionTest, APITestCase):

    casestudy = 17
    keyflow = 23
    actor = 5
    reason1_id = 3
    reason2_id = 5

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cs_url = cls.baseurl + reverse('casestudy-detail',
                                           kwargs=dict(pk=cls.casestudy))
        cls.url_key = "actor"
        cls.url_pks = dict(casestudy_pk=cls.casestudy, keyflow_pk=cls.keyflow)
        cls.url_pk = dict(pk=cls.actor)
        cls.post_data = dict(name='posttestname',
                             year=2017,
                             turnover='1000.00',
                             employees=2,
                             activity=1,
                             BvDid='141234',
                             reason=cls.reason1_id)
        cls.put_data = dict(name='posttestname',
                            year=2017,
                            turnover='1000.00',
                            employees=2,
                            activity=1,
                            BvDid='141234',
                            reason=cls.reason2_id)
        cls.patch_data = dict(name='patchtestname')

    def setUp(self):
        super().setUp()
        self.reason1 = ReasonFactory(id=self.reason1_id, reason='Reason 1')
        self.reason2 = ReasonFactory(id=self.reason2_id, reason='Reason 2')
        self.obj = ActorFactory(activity__activitygroup__keyflow=self.kic,
                                reason=self.reason1)

    def test_reason(self):
        """Test reason for exclusion"""
        url_reason = 'reason-list'
        response = self.get_check_200(url_reason)
        self.assertSetEqual({'Reason 1', 'Reason 2'},
                            {r['reason'] for r in response.data})

        data = {'reason': 'Reason 3', }
        response = self.post(url_reason, data=data)
        self.response_201(response)

        url = self.url_key + '-detail'
        kwargs = {'pk': self.obj.pk, **self.url_pks, }

        response = self.get_check_200(url, **kwargs)
        assert response.data['reason'] == self.reason1.id

        # change reason

        response = self.patch(url, **kwargs,
                              data={'reason': self.reason2.id, })
        self.response_200(response)
        assert response.data['reason'] == self.reason2.id

        # delete the reason
        url_reason = 'reason-detail'
        response = self.delete(url_reason, pk=self.reason2.id)
        self.response_204(response)

        # check if actors reason was set to null
        response = self.get_check_200(url, **kwargs)
        assert response.data['reason'] is None


class ActivityInCaseStudyTest(BasicModelPermissionTest, APITestCase):

    casestudy = 17
    activity = 5
    activitygroup = 90
    keyflow = 23

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ag_url = cls.baseurl + reverse(
            'activitygroup-detail',
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

    def test_unique_nacecode(self):
        """Test if the nace-code number is unique"""
        ag = ActivityGroup.objects.get(pk=self.activitygroup)
        ag2 = ActivityGroupFactory(keyflow__id=44)
        activity1 = Activity(activitygroup=ag, nace='E-01234', name='A1')
        activity2 = Activity(activitygroup=ag, nace='E-01235', name='A2')
        activity3 = Activity(activitygroup=ag, nace='V-01234', name='A3')
        activity1.save()
        activity2.save()
        # saving activity3 should raise the Validation error, because
        # the number 01234 already exists in nacecode E-01234
        with self.assertRaises(ValidationError):
            activity3.save()
        # in another keyflow, there may exist the same number once
        activity4 = Activity(activitygroup=ag2, nace='V-01234', name='A3')
        activity4.save()
        # but not twice
        activity5 = Activity(activitygroup=ag2, nace='G-01234', name='A3')
        with self.assertRaises(ValidationError):
            activity5.save()


class ActivitygroupInCaseStudyTest(BasicModelPermissionTest, APITestCase):

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

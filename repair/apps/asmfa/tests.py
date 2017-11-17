# -*- coding: utf-8 -*-

from django.test import TestCase
from django.core.validators import ValidationError
from django.contrib.gis.geos.point import Point
from django.urls import reverse
from django.core.serializers import serialize
from rest_framework.test import APIRequestFactory
from rest_framework.test import APITestCase
from rest_framework import status
from repair.tests.test import BasicModelTest


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
    Geolocation, 
    )


from repair.apps.login.models import CaseStudy, User, Profile
from repair.apps.login.factories import *
from repair.apps.asmfa.factories import *


class ASMFAModelTest(TestCase):

    fixtures = ['auth_fixture',
                'user_fixture.json',
                'activities_dummy_data.json',]

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
            Geolocation, 
            ):

            print('{} has {} test data entries'.format(
                Model, Model.objects.count()))

    def test_geolocation(self):
        """Test a geolocation"""
        point = Point(x=9.2, y=52.6, srid=4326)
        location = Geolocation(geom=point,
                               street='Hauptstraße')
        actor = Actor.objects.first()
        actor.administrative_location = location
        assert actor.administrative_location.geom.x == point.x

    def test_actor_included(self):
        """Test a geolocation"""
        actor = Actor.objects.first()
        actor.included = False
        actor.save()
        excluded_actors = Actor.objects.filter(included=False)
        # test that there is now at least one ignored actor 
        assert excluded_actors.count() > 0
        assert excluded_actors.first().included is False
        

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


class GeolocationViewTest(APITestCase):

    fixtures = ['auth_fixture', 'user_fixture.json',
                'activities_dummy_data.json']


    def test_locations(self):
        cs = CaseStudyFactory()
        url = reverse('geolocation-list', kwargs=dict(casestudy_pk=cs.pk))
        location = GeolocationFactory(casestudy=cs)
        data = {
            'street': location.street,
            'geom': location.geom.geojson}
        response = self.client.post(url, data, format='json')
        print(response)
        response = self.client.get(url)
        print(response.data)

    def test_get_location(self):
        lodz_pk = 3
        lodz = reverse('casestudy-detail', kwargs=dict(pk=lodz_pk))

        url = reverse('geolocation-list', kwargs=dict(casestudy_pk=lodz_pk))
        location = GeolocationFactory()
        data = {'street': 'Hauptstraße 13',
                'casestudy': lodz,
                'geom': location.geom.geojson,}
        response = self.client.post(url, data, format='json')
        print(response)
        new_geolocation_id = response.data['id']
        response = self.client.get(url)
        print(response.data)
        url = reverse('geolocation-detail', kwargs=dict(casestudy_pk=lodz_pk,
                                                        pk=new_geolocation_id))
        response = self.client.get(url)
        print(response.data)
        
        new_street = 'Dorfstraße 2'
        data = {'street': new_street,}
        self.client.patch(url, data)
        response = self.client.get(url)
        assert response.data['street'] == new_street

        # patch a geometry as geojson
        new_geom = Point(x=14, y=15, srid=4326)
        data = {'geom': new_geom.geojson,}
        self.client.patch(url, data)
        response = self.client.get(url)
        geom = response.data['geom']
        assert str(geom) == new_geom.geojson
        assert geom['coordinates'] == [new_geom.x, new_geom.y]

        # patch a geometry in EWKT format
        new_geom_ewkt = 'SRID=4269;POINT(-71.064544 42.28787)'
        data = {'geom': new_geom_ewkt,}
        self.client.patch(url, data)
        response = self.client.get(url)
        geom = response.data['geom']
        assert geom['coordinates'] == [-71.064544, 42.28787]


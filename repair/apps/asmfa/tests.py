# -*- coding: utf-8 -*-

from django.test import TestCase
from django.core.validators import ValidationError
from django.contrib.gis.geos.point import Point


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

from repair.apps.login.models import CaseStudy


class ModelTest(TestCase):

    fixtures = ['user_fixture.json',
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
# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.gis.geos.point import Point

from repair.apps.asmfa.models import Actor
from repair.apps.asmfa.factories import (ActorFactory,
                                         AdministrativeLocationFactory)


class ASMFAModelTest(TestCase):

    def test_geolocation(self):
        """Test a geolocation"""
        point = Point(x=9.2, y=52.6, srid=4326)
        location = AdministrativeLocationFactory(geom=point,
                                                 address='Hauptstraße')
        actor = location.actor
        # assert that One2One Relationship works between actor and location
        self.assertEqual(location, actor.administrative_location)
        # assert that the geometry of the point was correctly added
        assert actor.administrative_location.geom.x == point.x

    def test_actor_included(self):
        """Test a geolocation"""
        actor1 = ActorFactory(included=True)
        actor2 = ActorFactory(included=True)
        actor1.included = False
        actor1.save()
        excluded_actors = Actor.objects.filter(included=False)
        # test that there is now at least one ignored actor
        assert excluded_actors.count() > 0
        assert excluded_actors.first().included is False

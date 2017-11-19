# -*- coding: utf-8 -*-

from django.test import TestCase
#from django.db.models.fields.related_descriptors import (
    #RelatedObjectDoesNotExist)
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
    AdministrativeLocation,
    OperationalLocation, 
    )


from repair.apps.login.models import CaseStudy, User, Profile
from repair.apps.login.factories import CaseStudyFactory
from repair.apps.asmfa.factories import (MaterialFactory,
                                         QualityFactory,
                                         GeolocationFactory,
                                         AdministrativeLocationFactory,
                                         OperationalLocationFactory,
                                         )
                                         


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
            Group2Group,
            GroupStock,
            AdministrativeLocation,
            OperationalLocation, 
            ):

            print('{} has {} test data entries'.format(
                Model, Model.objects.count()))

    def test_geolocation(self):
        """Test a geolocation"""
        point = Point(x=9.2, y=52.6, srid=4326)
        location = AdministrativeLocation(geom=point,
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

    def test_administrative_location(self):
        """Test creating, updating and deleting of administrative locations"""
        # create administrative location with actor and casestudy
        location = AdministrativeLocationFactory()
        cs = location.casestudy.pk
        actor = location.actor
        
        # define the urls
        url_locations = reverse('administrativelocation-list',
                                kwargs={'casestudy_pk': cs})

        url_locations_detail = reverse(
            'administrativelocation-detail',
            kwargs={'casestudy_pk': cs,
                    'pk': location.pk,})
        url_actor = reverse('actor-detail',
                            kwargs={'casestudy_pk': cs,
                                    'pk': actor.pk,})

        # list the activity locations and assert that it contains 
        # the new one 
        response = self.client.get(url_locations)
        assert response.status_code == 200
        assert location.pk in (row['id'] for row in response.data['features'])
        
        # update existing administrative location with a patch for actor
        new_streetname = 'Hauptstraße 13'
        data = {'administrative_location_geojson':
                {'street': new_streetname,
                 'geom': location.geom.geojson,
                 }
                }
        response = self.client.patch(url_actor, data, format='json')
        print(response.status_text)
        assert response.status_code == 200
        
        # get the new adress
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['street'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [location.geom.x, location.geom.y]

        # delete location
        response = self.client.delete(url_locations_detail)
        assert response.status_code == 204

        # should not exist any more in the database
        response = self.client.get(url_locations_detail)
        assert response.status_code == 404
        #actor.refresh_from_db(fields=['administrative_location'])
        actor = Actor.objects.get(pk=actor.pk)
        with self.assertRaises(actor.__class__.administrative_location.\
                               RelatedObjectDoesNotExist) as e:
            loc = actor.administrative_location
        
        # post new administrative location
        new_streetname = 'Dorfstraße 2'
        new_geom = Point(x=14, y=15, srid=4326)
        data = {'administrative_location_geojson':
                {'street': new_streetname,
                     'geom': new_geom.geojson,
                    }
                }
        response = self.client.patch(url_actor, data, format='json')
        assert response.status_code == 200
        new_aloc_id = response.data['administrative_location_geojson']['id']
        
        url_locations_detail = reverse(
            'administrativelocation-detail',
            kwargs={'casestudy_pk': cs,
                    'pk': new_aloc_id,})        
    
        # get the new location and check the coordinates and the street
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['street'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom.x, new_geom.y]

        # patch a geometry in EWKT format directly in the locations table
        new_geom_ewkt = 'SRID=4269;POINT(100 -11)'
        data = {'geom' : new_geom_ewkt}
        response = self.client.patch(url_locations_detail, data)
        assert response.status_code == 200

        # test if new coordinates appear at the actor locations
        response = self.client.get(url_actor)        
        geom = response.data['administrative_location_geojson']['geometry']
        assert geom['coordinates'] == [100, -11]
        
    def test_operational_locations(self):
        """Test creating, updating and deleting of operational locations"""

        def get_location_url(cs, location):
            url_locations_detail = reverse(
                'operationallocation-detail',
                kwargs={'casestudy_pk': cs,
                        'pk': location,})
            return url_locations_detail

        # create 2 operational location with actor and casestudy
        location1 = OperationalLocationFactory()
        cs = location1.casestudy.pk
        actor = location1.actor
        location2 = OperationalLocationFactory(actor=actor)
        
        # define the urls
        url_locations = reverse('operationallocation-list',
                                kwargs={'casestudy_pk': cs})

        url_actor = reverse('actor-detail',
                            kwargs={'casestudy_pk': cs,
                                    'pk': actor.pk,})

        # list the activity locations and assert that it contains 
        # the new one 
        response = self.client.get(url_locations)
        assert response.status_code == 200
        assert location1.pk in (row['id'] for row in response.data['features'])
        assert location2.pk in (row['id'] for row in response.data['features'])

        
        response = self.client.get(url_actor)
        print(response.data['operational_locations_geojson'])
        
        
        # update existing operational location with a put for actor
        new_streetname2 = 'Hauptstraße 13'
        new_streetname3 = 'Dorfstraße 15'
        new_geom2 = Point(x=2, y=3, srid=4326)
        new_geom3 = Point(x=4, y=5, srid=4326)
        data = {'operational_locations_geojson': [
            # update the first location
                {'street': new_streetname2,
                 'geom': new_geom2.geojson,
                 'id': location2.id,
                 'turnover': 99987.12,
                 },
                # create a new location (no id provided)
                {'street': new_streetname3,
                 'geom': new_geom3.geojson,
                 'employees': 123,
                 },
                # delete the second location (not in the new list any more)
        ]
                }
        response = self.client.patch(url_actor, data, format='json')
        print(response.status_text)
        assert response.status_code == 200
        new_location_ids = [feature['id'] for feature in 
            response.data['operational_locations_geojson']['features']]
        
        # check the new adress of the location2
        url = get_location_url(cs, location=new_location_ids[0])
        response = self.client.get(url)
        properties = response.data['properties']
        assert properties['street'] == new_streetname2
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom2.x, new_geom2.y]

        # check the new adress of the location3
        url = get_location_url(cs, location=new_location_ids[1])
        response = self.client.get(url)
        properties = response.data['properties']
        assert properties['street'] == new_streetname3
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom3.x, new_geom3.y]

        # delete location 2
        url = get_location_url(cs, location=new_location_ids[0])
        response = self.client.delete(url)
        assert response.status_code == 204

        # should not exist any more in the database
        #actor.refresh_from_db(fields=['administrative_location'])
        actor = Actor.objects.get(pk=actor.pk)
        olocs = actor.operational_locations
        assert olocs.count() == 1
        
        # existing locations
        response = self.client.get(url_actor)
        features = response.data['operational_locations_geojson']['features']

        # post new administrative location
        new_streetname = 'Pecsallée 4'
        new_geom = Point(x=8, y=10, srid=4326)
        features.append({'street': new_streetname,
                         'geom': new_geom.geojson,
                         })
        
        data = {'operational_locations_geojson': features}
        response = self.client.patch(url_actor, data, format='json')
        assert response.status_code == 200
        new_features = response.data['operational_locations_geojson']['features']
        new_ids = [feature['id'] for feature in new_features]
        
        url_locations_detail = reverse(
            'operationallocation-detail',
            kwargs={'casestudy_pk': cs,
                    'pk': new_ids[1],})        
    
        # get the new location and check the coordinates and the street
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['street'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom.x, new_geom.y]


        # patch a geometry in EWKT format directly in the locations table
        new_geom_ewkt = 'SRID=4326;POINT(6 5)'
        data = {'geom' : new_geom_ewkt}
        response = self.client.patch(url_locations_detail, data)
        assert response.status_code == 200

        # test if new coordinates appear at the actor locations
        response = self.client.get(url_actor)        
        features = response.data['operational_locations_geojson']['features']
        feature5_geom = features[1]['geometry']
        assert feature5_geom['coordinates'] == [6, 5]


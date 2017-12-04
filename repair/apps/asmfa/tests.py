# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.gis.geos.point import Point
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from repair.tests.test import BasicModelTest
from rest_framework import status



from repair.apps.asmfa.models import (
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
    )


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
                                          address='Hauptstraße')
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


class KeyflowTest(BasicModelTest, APITestCase):
    casestudy = 17

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cs_url = cls.baseurl + reverse('casestudy-detail',
                                           kwargs=dict(pk=cls.casestudy))
        cls.url_key = "keyflow"
        cls.url_pks = dict()
        cls.url_pk = dict(pk=1)
        cls.post_data = dict(name='posttestname',
                             casestudies=[cls.cs_url], code='cdo')
        cls.put_data = dict(name='puttestname',
                            casestudies=[cls.cs_url])
        cls.patch_data = dict(name='patchtestname')

    def setUp(self):
        self.obj = KeyflowFactory()


class KeyflowInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    keyflow = 3
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cs_url = cls.baseurl + reverse('casestudy-detail',
                                   kwargs=dict(pk=cls.casestudy))
        cls.keyflow_url = cls.baseurl + reverse('keyflow-detail',
                                                 kwargs=dict(pk=cls.keyflow))


        cls.url_key = keyflowincasestudy"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.keyflow)

        cls.put_data = dict(note='new_put_note',
                             keyflow=cls.keyflow_url,
                             )
        cls.post_data = dict(note='new_note',
                             keyflow=cls.keyflow,
                             )

        cls.patch_data = dict(note='patchtestnote')

    def setUp(self):
        self.obj = KeyflowInCasestudyFactory(casestudy=self.uic.casestudy,
                                              keyflow__id=self.keyflow)

    def test_post(self):
        url = reverse(self.url_key +'-list', kwargs=self.url_pks)
        # post
        response = self.client.post(url, self.post_data)
        for key in self.post_data:
            assert response.data[key] == self.post_data[key]
        assert response.status_code == status.HTTP_201_CREATED


class ActorInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    actor = 5
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cs_url = cls.baseurl + reverse('casestudy-detail',
                                       kwargs=dict(pk=cls.casestudy))
        cls.url_key = "actor"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.actor)
        cls.post_data = dict(name='posttestname', year=2017, revenue=1000,
                             employees=2, activity=1)
        cls.put_data = dict(name='posttestname', year=2017, revenue=1000,
                            employees=2, activity=1)
        cls.patch_data = dict(name='patchtestname')


    def setUp(self):
        self.obj = ActorFactory(activity__activitygroup__casestudy=self.uic.casestudy)


class ActivityInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    activity = 5
    activitygroup = 90
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ag_url = cls.baseurl + reverse('activitygroup-detail',
                                           kwargs=dict(pk=cls.activity,
                                                       casestudy_pk=cls.casestudy))
        cls.url_key = "activity"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.activity)
        cls.post_data = dict(nace="Test Nace",
                             name="Test Name",
                             activitygroup=cls.activitygroup)
        cls.put_data = dict(nace="Test Nace",
                             name="Test Name",
                             activitygroup=cls.activitygroup)
        cls.patch_data = dict(name='Test Name')


    def setUp(self):
        self.obj = ActivityFactory(
            activitygroup__casestudy=self.uic.casestudy,
            activitygroup__id=self.activitygroup)


class ActivitygroupInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    activitygroup = 90
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        #cls.ag_url = cls.baseurl + reverse('activitygroup-detail',
                                           #kwargs=dict(pk=cls.activity,
                                                       #casestudy_pk=cls.casestudy))
        cls.url_key = "activitygroup"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.activitygroup)
        cls.post_data = dict(code="Test Code", name='P1')
        cls.put_data = dict(code="Test Code", name='P1')
        cls.patch_data = dict(name='P1')


    def setUp(self):
        self.obj = ActivityGroupFactory(casestudy=self.uic.casestudy)

    def test_post(self):
        """
        not sure: Matching query does not exist
        """
        pass


class ActivityInActivitygroupInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    activity = 5
    activitygroup = 90
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ag_url = cls.baseurl + reverse('activitygroup-detail',
                                           kwargs=dict(pk=cls.activity,
                                                       casestudy_pk=cls.casestudy))
        cls.url_key = "activity"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
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
        self.obj = ActivityFactory(
            activitygroup__casestudy=self.uic.casestudy,
            activitygroup__id=self.activitygroup)




class QualityTest(BasicModelTest, APITestCase):

    url_key = "quality"
    url_pks = dict()
    url_pk = dict(pk=1)
    post_data = dict(name='posttestname')
    put_data = dict(name='puttestname')
    patch_data = dict(name='patchtestname')

    def setUp(self):
        self.obj = QualityFactory()


class GeolocationViewTest(APITestCase):

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
        url_actor = self.get_url_actor(cs, actor)

        # list the activity locations and assert that it contains
        # the new one
        response = self.client.get(url_locations)
        assert response.status_code == status.HTTP_200_OK
        assert location.pk in (row['id'] for row in response.data['features'])

        # update existing administrative location with a patch for actor
        new_streetname = 'Hauptstraße 13'
        data = {'administrative_location_geojson':
                {'address': new_streetname,
                 'geom': location.geom.geojson,
                 }
                }
        response = self.client.patch(url_actor, data, format='json')
        print(response.status_text)
        assert response.status_code == status.HTTP_200_OK

        # get the new adress
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['address'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [location.geom.x, location.geom.y]

        # delete location
        response = self.client.delete(url_locations_detail)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # should not exist any more in the database
        response = self.client.get(url_locations_detail)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        #actor.refresh_from_db(fields=['administrative_location'])
        actor = Actor.objects.get(pk=actor.pk)
        with self.assertRaises(actor.__class__.administrative_location.\
                               RelatedObjectDoesNotExist) as e:
            loc = actor.administrative_location

        # post new administrative location
        new_streetname = 'Dorfstraße 2'
        new_geom = Point(x=14, y=15, srid=4326)
        data = {'administrative_location_geojson':
                {'address': new_streetname,
                     'geom': new_geom.geojson,
                    }
                }
        response = self.client.patch(url_actor, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        new_aloc_id = response.data['administrative_location_geojson']['id']

        url_locations_detail = reverse(
            'administrativelocation-detail',
            kwargs={'casestudy_pk': cs,
                    'pk': new_aloc_id,})

        # get the new location and check the coordinates and the street
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['address'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom.x, new_geom.y]

        # patch a geometry in EWKT format directly in the locations table
        new_geom_ewkt = 'SRID=4269;POINT(100 -11)'
        data = {'geom' : new_geom_ewkt}
        response = self.client.patch(url_locations_detail, data)
        assert response.status_code == status.HTTP_200_OK

        # test if new coordinates appear at the actor locations
        response = self.client.get(url_actor)
        geom = response.data['administrative_location_geojson']['geometry']
        assert geom['coordinates'] == [100, -11]

    def get_url_actor(self, cs, actor):
        url_actor = reverse('actor-detail', kwargs={'casestudy_pk': cs,
                                                    'pk': actor.pk,})
        return url_actor

    @staticmethod
    def get_location_url(cs, location):
        url_locations_detail = reverse(
            'operationallocation-detail',
            kwargs={'casestudy_pk': cs,
                    'pk': location,})
        return url_locations_detail

    def test_operational_locations(self):
        """Test creating, updating and deleting of operational locations"""

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
        assert response.status_code == status.HTTP_200_OK
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
                {'address': new_streetname2,
                 'geom': new_geom2.geojson,
                 'id': location2.id,
                 'turnover': 99987.12,
                 },
                # create a new location (no id provided)
                {'address': new_streetname3,
                 'geom': new_geom3.geojson,
                 'employees': 123,
                 },
                # delete the second location (not in the new list any more)
        ]
                }
        response = self.client.patch(url_actor, data, format='json')
        print(response.status_text)
        assert response.status_code == status.HTTP_200_OK
        new_location_ids = [feature['id'] for feature in
            response.data['operational_locations_geojson']['features']]

        # check the new adress of the location2
        url = self.get_location_url(cs, location=new_location_ids[0])
        response = self.client.get(url)
        properties = response.data['properties']
        assert properties['address'] == new_streetname2
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom2.x, new_geom2.y]

        # check the new adress of the location3
        url = self.get_location_url(cs, location=new_location_ids[1])
        response = self.client.get(url)
        properties = response.data['properties']
        assert properties['address'] == new_streetname3
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom3.x, new_geom3.y]

        # delete location 2
        url = self.get_location_url(cs, location=new_location_ids[0])
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

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
        features.append({'address': new_streetname,
                         'geom': new_geom.geojson,
                         })

        data = {'operational_locations_geojson': features}
        response = self.client.patch(url_actor, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        new_features = response.data['operational_locations_geojson']['features']
        new_ids = [feature['id'] for feature in new_features]

        url_locations_detail = reverse(
            'operationallocation-detail',
            kwargs={'casestudy_pk': cs,
                    'pk': new_ids[1],})

        # get the new location and check the coordinates and the street
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['address'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom.x, new_geom.y]


        # patch a geometry in EWKT format directly in the locations table
        new_geom_ewkt = 'SRID=4326;POINT(6 5)'
        data = {'geom' : new_geom_ewkt}
        response = self.client.patch(url_locations_detail, data)
        assert response.status_code == status.HTTP_200_OK

        # test if new coordinates appear at the actor locations
        response = self.client.get(url_actor)
        features = response.data['operational_locations_geojson']['features']
        feature5_geom = features[1]['geometry']
        assert feature5_geom['coordinates'] == [6, 5]


class TestLocationsOfActor(APITestCase):

    @staticmethod
    def get_adminlocation_url(cs, location, actor):
        url_locations_detail = reverse(
            'administrativelocation-detail',
            kwargs={'casestudy_pk': cs,
                    'actor_pk': actor,
                    'pk': location,})
        return url_locations_detail

    def test_administrative_location(self):
        """Test creating, updating and deleting of administrative locations"""
        # create administrative location with actor and casestudy
        location = AdministrativeLocationFactory()
        cs = location.casestudy.pk
        actor = location.actor

        # define the urls
        url_locations = reverse('administrativelocation-list',
                                kwargs={'casestudy_pk': cs,
                                        'actor_pk': actor.pk,})

        url_actor = self.get_url_actor(cs, actor)

        # list the activity locations and assert that it contains
        # the new one
        response = self.client.get(url_locations)
        assert response.status_code == status.HTTP_200_OK
        assert location.pk in (row['id'] for row in response.data['features'])

        # update existing administrative location with a patch for actor
        new_streetname = 'Hauptstraße 13'
        data = {'address': new_streetname,
                 'geom': location.geom.geojson,
                 }
        response = self.client.post(url_locations, data, format='json')
        print(response.status_text)
        assert response.status_code == status.HTTP_201_CREATED
        new_aloc_id = response.data['id']

        url_locations_detail = self.get_adminlocation_url(cs, new_aloc_id,
                                                              actor.pk)

        # get the new adress
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['address'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [location.geom.x, location.geom.y]

        # update administrative location
        new_streetname = 'Dorfstraße 2'
        new_geom = Point(x=14, y=15, srid=4326)
        data = {'address': new_streetname,
                     'geom': new_geom.geojson,
                    }
        response = self.client.post(url_locations, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        new_aloc_id = response.data['id']

        url_locations_detail = self.get_adminlocation_url(cs, new_aloc_id,
                                                          actor.pk)


        # get the new location and check the coordinates and the street
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['address'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom.x, new_geom.y]

        # patch a geometry in EWKT format directly in the locations table
        new_geom_ewkt = 'SRID=4269;POINT(100 -11)'
        data = {'geom' : new_geom_ewkt}
        response = self.client.patch(url_locations_detail, data)
        assert response.status_code == status.HTTP_200_OK

        # test if new coordinates appear at the actor locations
        response = self.client.get(url_actor)
        geom = response.data['administrative_location_geojson']['geometry']
        assert geom['coordinates'] == [100, -11]

    def get_url_actor(self, cs, actor):
        url_actor = reverse('actor-detail', kwargs={'casestudy_pk': cs,
                                                    'pk': actor.pk,})
        return url_actor

    @staticmethod
    def get_location_url(cs, location, actor):
        url_locations_detail = reverse(
            'operationallocation-detail',
            kwargs={'casestudy_pk': cs,
                    'actor_pk': actor,
                    'pk': location,})
        return url_locations_detail

    def test_operational_locations(self):
        """Test creating, updating and deleting of operational locations"""

        # create 2 operational location with actor and casestudy
        location1 = OperationalLocationFactory()
        cs = location1.casestudy.pk
        actor = location1.actor
        location2 = OperationalLocationFactory(actor=actor)

        # define the urls
        url_locations = reverse('operationallocation-list',
                                kwargs={'casestudy_pk': cs,
                                        'actor_pk': actor.pk,})

        url_actor = reverse('actor-detail',
                            kwargs={'casestudy_pk': cs,
                                    'pk': actor.pk,})

        # list the activity locations and assert that it contains
        # the new one
        response = self.client.get(url_locations)
        assert response.status_code == status.HTTP_200_OK
        assert location1.pk in (row['id'] for row in response.data['features'])
        assert location2.pk in (row['id'] for row in response.data['features'])


        response = self.client.get(url_actor)
        print(response.data['operational_locations_geojson'])

        response = self.client.get(url_locations)

        # update existing operational location with a put for actor
        new_streetname2 = 'Hauptstraße 13'
        new_streetname3 = 'Dorfstraße 15'
        new_geom2 = Point(x=2, y=3, srid=4326)
        new_geom3 = Point(x=4, y=5, srid=4326)
        data = {'type': 'FeatureCollection',
                'features': [
            # update the first location
                {'geom': new_geom2.geojson,
                 'id': location2.id,
                 'turnover': 99987.12,
                 'address': new_streetname2,
                 },
                # create a new location (no id provided)
                {'geom': new_geom3.geojson,
                 'employees': 123,
                 'address': new_streetname3,
                 },
                # delete the second location (not in the new list any more)
        ]}
        response = self.client.post(url_locations, data, format='json')
        print(response.status_text)
        assert response.status_code == status.HTTP_201_CREATED
        response = self.client.get(url_locations)
        new_location_ids = [feature['id'] for feature in
            response.data['features']]

        # check the new adress of the location2
        url = self.get_location_url(cs, location=new_location_ids[0],
                                    actor=actor.pk)
        response = self.client.get(url)
        properties = response.data['properties']
        assert properties['address'] == new_streetname2
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom2.x, new_geom2.y]

        # check the new adress of the location3
        url = self.get_location_url(cs, location=new_location_ids[1],
                                    actor=actor.pk)
        response = self.client.get(url)
        properties = response.data['properties']
        assert properties['address'] == new_streetname3
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom3.x, new_geom3.y]

        # delete location 2
        url = self.get_location_url(cs, location=new_location_ids[0],
                                    actor=actor.pk)
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # should not exist any more in the database
        #actor.refresh_from_db(fields=['administrative_location'])
        actor = Actor.objects.get(pk=actor.pk)
        olocs = actor.operational_locations
        assert olocs.count() == 1

        # existing locations
        response = self.client.get(url_locations)
        feature_collection = response.data
        features = feature_collection['features']

        # post new operational location
        new_streetname = 'Pecsallée 4'
        new_geom = Point(x=8, y=10, srid=4326)
        features.append({'address': new_streetname,
                         'geom': new_geom.geojson,
                         })

        data = feature_collection
        response = self.client.post(url_locations, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        response = self.client.get(url_locations)
        new_ids = [feature['id'] for feature in
            response.data['features']]

        url_locations_detail = self.get_location_url(cs, location=new_ids[1],
                                                     actor=actor.pk)

        # get the new location and check the coordinates and the street
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['address'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom.x, new_geom.y]


        # patch a geometry in EWKT format directly in the locations table
        new_geom_ewkt = 'SRID=4326;POINT(6 5)'
        data = {'geom' : new_geom_ewkt}
        response = self.client.patch(url_locations_detail, data)
        assert response.status_code == status.HTTP_200_OK

        # test if new coordinates appear at the actor locations
        response = self.client.get(url_actor)
        features = response.data['operational_locations_geojson']['features']
        feature5_geom = features[1]['geometry']
        assert feature5_geom['coordinates'] == [6, 5]

        # add a single location

        # post oe new operational location
        new_streetname = 'Napoliroad 4333'
        new_geom = Point(x=3, y=2, srid=4326)
        data = {'address': new_streetname,
                'geom': new_geom.geojson,
                }
        response = self.client.post(url_locations, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        new_id = response.data['id']
        url_locations_detail = self.get_location_url(cs, location=new_id,
                                                         actor=actor.pk)

        response = self.client.get(url_locations_detail)
        assert response.status_code == status.HTTP_200_OK
        geom = response.data['geometry']
        self.assertJSONEqual(str(geom), new_geom.geojson)
        assert response.data['properties']['address'] == new_streetname

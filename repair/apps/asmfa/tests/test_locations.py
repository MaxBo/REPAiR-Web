# -*- coding: utf-8 -*-

from django.contrib.gis.geos.point import Point
from django.urls import reverse
from rest_framework import status
from test_plus import APITestCase
from repair.tests.test import LoginTestCase

from repair.apps.login.models import CaseStudy
from repair.apps.asmfa.models import Actor
from repair.apps.asmfa.factories import (AdministrativeLocationFactory,
                                         OperationalLocationFactory)
from repair.apps.studyarea.factories import AreaFactory


class GeolocationViewTest(LoginTestCase, APITestCase):

    def test_administrative_location(self):
        """Test creating, updating and deleting of administrative locations"""
        # create administrative location with actor and casestudy
        location = AdministrativeLocationFactory()

        delft, rotterdam = self.define_areas(location)

        cs = location.casestudy.pk
        keyflow = location.keyflow.pk
        actor = location.actor

        # add access to casestudy
        casestudy = CaseStudy.objects.get(id=cs)
        casestudy.userincasestudy_set.add(self.uic)

        # define the urls
        url_locations = reverse('administrativelocation-list',
                                kwargs={'casestudy_pk': cs,
                                        'keyflow_pk': keyflow, })

        url_locations_detail = reverse(
            'administrativelocation-detail',
            kwargs={'casestudy_pk': cs,
                    'keyflow_pk': keyflow,
                    'pk': location.pk, })

        # list the activity locations and assert that it contains
        # the new one
        response = self.client.get(url_locations)
        assert response.status_code == status.HTTP_200_OK
        res_data = response.data['results']
        assert location.pk in (row['id'] for row in res_data['features'])

        # patch existing administrative location
        new_streetname = 'Hauptstraße 13'
        data = {'properties': {'address': new_streetname,
                               'area': delft.pk, },
                'geometry': location.geom.geojson
                }
        response = self.client.patch(url_locations_detail, data, format='json')
        assert response.status_code == status.HTTP_200_OK

        # get the new adress
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['address'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [location.geom.x, location.geom.y]
        assert properties['area'] == delft.pk
        assert properties['level'] == delft.adminlevel_id

        # delete location
        response = self.client.delete(url_locations_detail)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # should not exist any more in the database
        response = self.client.get(url_locations_detail)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        actor = Actor.objects.get(pk=actor.pk)
        with self.assertRaises(
            actor.__class__.administrative_location.RelatedObjectDoesNotExist
            ) as e:
            loc = actor.administrative_location

        # post new administrative location
        new_streetname = 'Dorfstraße 2'
        new_geom = Point(x=14, y=15, srid=4326)
        data = {'properties':
                {'address': new_streetname,
                 'actor': actor.id,
                 'area': rotterdam.pk, },
                'geometry': new_geom.geojson
                }
        response = self.client.post(url_locations, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        new_aloc_id = response.data['id']

        # deny uploading a second administrative location
        response = self.client.post(url_locations, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        url_locations_detail = reverse(
            'administrativelocation-detail',
            kwargs={'casestudy_pk': cs,
                    'keyflow_pk': keyflow,
                    'pk': new_aloc_id, })

        # get the new location and check the coordinates and the street
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['address'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom.x, new_geom.y]
        assert properties['area'] == rotterdam.pk

        # patch a geometry in EWKT format directly in the locations table
        new_geom_ewkt = 'SRID=4269;POINT(100 -11)'
        data = {'geom': new_geom_ewkt}
        response = self.client.patch(url_locations_detail, data)
        assert response.status_code == status.HTTP_200_OK

        response = self.client.get(url_locations_detail)
        geom = response.data['geometry']
        assert geom['coordinates'] == [100, -11]

    @staticmethod
    def define_areas(location):
        # create areas
        zuidholland = AreaFactory(
            adminlevel__level=4,
            adminlevel__name='Province',
            adminlevel__casestudy_id=location.casestudy.pk,
            name='Zuid-Holland')
        delft = AreaFactory(adminlevel__level=6,
                            adminlevel__name='Gemeende',
                            name='Delft',
                            parent_area=zuidholland)
        rotterdam = AreaFactory(adminlevel__level=6,
                                name='Rotterdam',
                                parent_area=zuidholland)
        return delft, rotterdam

    @staticmethod
    def get_location_url(cs, keyflow, location):
        url_locations_detail = reverse(
            'operationallocation-detail',
            kwargs={'casestudy_pk': cs,
                    'keyflow_pk': keyflow,
                    'pk': location, })
        return url_locations_detail

    def test_operational_locations(self):
        """Test creating, updating and deleting of operational locations"""

        # create 2 operational location with actor and casestudy
        location1 = OperationalLocationFactory()
        cs = location1.casestudy.pk
        keyflow = location1.keyflow.pk
        actor = location1.actor
        location2 = OperationalLocationFactory(actor=actor)

        delft, rotterdam = self.define_areas(location1)

        # add access to casestudy
        casestudy = CaseStudy.objects.get(id=cs)
        casestudy.userincasestudy_set.add(self.uic)

        # define the urls
        url_locations = reverse('operationallocation-list',
                                kwargs={'casestudy_pk': cs,
                                        'keyflow_pk': keyflow, })

        # list the activity locations and assert that it contains
        # the new one
        response = self.client.get(url_locations)
        assert response.status_code == status.HTTP_200_OK
        assert location1.pk in (row['id'] for row in response.data['results']['features'])
        assert location2.pk in (row['id'] for row in response.data['results']['features'])

        # patch location1
        url_locations_detail = self.get_location_url(cs, keyflow,
                                                     location=location1.id)
        new_location = Point(x=2, y=3, srid=4326)
        new_streetname = 'Hauptstraße 13'
        data = {'properties': {'address': new_streetname,
                               'area': rotterdam.pk, },
                'geometry': new_location.geojson
                }
        response = self.client.patch(url_locations_detail, data, format='json')
        assert response.status_code == status.HTTP_200_OK

        # check the new adress of the location1
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['address'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_location.x, new_location.y]
        assert properties['area'] == rotterdam.pk
        assert properties['level'] == rotterdam.adminlevel_id

        # delete location 2
        url_locations_detail = self.get_location_url(cs, keyflow,
                                                     location=location2.id)
        response = self.client.delete(url_locations_detail)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # should not exist any more in the database
        response = self.client.get(url_locations_detail)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # post new operational location
        new_streetname = 'Pecsallée 4'
        new_geom = Point(x=8, y=10, srid=4326)
        zuid_holland = rotterdam.parent_area
        data = {'properties':
                {'address': new_streetname,
                 'actor': actor.id,
                 'area': zuid_holland.pk, },
                'geometry': new_geom.geojson}

        response = self.client.post(url_locations, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        new_oloc_id = response.data['id']

        url_locations_detail = reverse(
            'operationallocation-detail',
            kwargs={'casestudy_pk': cs,
                    'keyflow_pk': keyflow,
                    'pk': new_oloc_id, })

        # get the new location and check the coordinates and the street
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['address'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom.x, new_geom.y]
        assert properties['area'] == zuid_holland.pk
        assert properties['level'] == zuid_holland.adminlevel_id

        # patch a geometry in EWKT format directly in the locations table
        new_geom_ewkt = 'SRID=4326;POINT(6 5)'
        data = {'geom': new_geom_ewkt,
                'area': delft.pk, }
        response = self.client.patch(url_locations_detail, data)
        assert response.status_code == status.HTTP_200_OK

        response = self.client.get(url_locations_detail)
        geom = response.data['geometry']
        assert geom['coordinates'] == [6, 5]
        properties = response.data['properties']
        assert properties['area'] == delft.pk


class TestLocationsOfActor(LoginTestCase, APITestCase):

    @staticmethod
    def get_adminlocation_url(cs, keyflow, location, actor):
        url_locations_detail = reverse(
            'administrativelocation-detail',
            kwargs={'casestudy_pk': cs,
                    'keyflow_pk': keyflow,
                    'actor_pk': actor,
                    'pk': location, })
        return url_locations_detail

    def test_administrative_location(self):
        """Test creating, updating and deleting of administrative locations"""
        # create administrative location with actor and casestudy
        location = AdministrativeLocationFactory()
        cs = location.casestudy.pk
        keyflow = location.keyflow.pk
        actor = location.actor

        # add access to casestudy
        casestudy = CaseStudy.objects.get(id=cs)
        casestudy.userincasestudy_set.add(self.uic)

        # define the urls
        url_locations = reverse('administrativelocation-list',
                                kwargs={'casestudy_pk': cs,
                                        'keyflow_pk': keyflow,
                                        'actor_pk': actor.pk, })

        # list the activity locations and assert that it contains
        # the new one
        response = self.client.get(url_locations)
        assert response.status_code == status.HTTP_200_OK
        assert location.pk in (row['id'] for row in response.data['results']['features'])

        # update existing administrative location with a patch for actor
        new_streetname = 'Hauptstraße 13'
        data = {'address': new_streetname,
                 'geom': location.geom.geojson,
                 'actor': actor.id,
                }
        response = self.client.post(url_locations, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        new_aloc_id = response.data['id']

        url_locations_detail = self.get_adminlocation_url(cs, keyflow,
                                                          new_aloc_id,
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
                'geom': new_geom.geojson
                }
        response = self.client.post(url_locations, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        new_aloc_id = response.data['id']

        url_locations_detail = self.get_adminlocation_url(cs, keyflow,
                                                          new_aloc_id,
                                                          actor.pk)

        # get the new location and check the coordinates and the street
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['address'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom.x, new_geom.y]

        # patch a geometry in EWKT format directly in the locations table
        new_geom_ewkt = 'SRID=4269;POINT(100 -11)'
        data = {'geom': new_geom_ewkt}
        response = self.client.patch(url_locations_detail, data)
        assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def get_location_url(cs, keyflow, location, actor):
        url_locations_detail = reverse(
            'operationallocation-detail',
            kwargs={'casestudy_pk': cs,
                    'keyflow_pk': keyflow,
                    'actor_pk': actor,
                    'pk': location, })
        return url_locations_detail

    def test_operational_locations(self):
        """Test creating, updating and deleting of operational locations"""

        # create 2 operational location with actor and casestudy
        location1 = OperationalLocationFactory()
        cs = location1.casestudy.pk
        keyflow = location1.keyflow.pk
        actor = location1.actor
        location2 = OperationalLocationFactory(actor=actor)

        # add access to casestudy
        casestudy = CaseStudy.objects.get(id=cs)
        casestudy.userincasestudy_set.add(self.uic)

        # define the urls
        url_locations = reverse('operationallocation-list',
                                kwargs={'casestudy_pk': cs,
                                        'keyflow_pk': keyflow,
                                        'actor_pk': actor.pk, })

        # list the activity locations and assert that it contains
        # the new one
        response = self.client.get(url_locations)
        assert response.status_code == status.HTTP_200_OK
        assert location1.pk in (row['id'] for row in
                                response.data['results']['features'])
        assert location2.pk in (row['id'] for row in
                                response.data['results']['features'])

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
        assert response.status_code == status.HTTP_201_CREATED
        response = self.client.get(url_locations)
        new_location_ids = [feature['id'] for feature in
                            response.data['results']['features']]

        # check the new adress of the location2
        url = self.get_location_url(cs, keyflow,
                                    location=new_location_ids[0],
                                    actor=actor.pk)
        response = self.client.get(url)
        properties = response.data['properties']
        assert properties['address'] == new_streetname2
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom2.x, new_geom2.y]

        # check the new adress of the location3
        url = self.get_location_url(cs, keyflow,
                                    location=new_location_ids[1],
                                    actor=actor.pk)
        response = self.client.get(url)
        properties = response.data['properties']
        assert properties['address'] == new_streetname3
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom3.x, new_geom3.y]

        # delete location 2
        url = self.get_location_url(cs, keyflow,
                                    location=new_location_ids[0],
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
        features = feature_collection['results']['features']

        # post new operational location
        new_streetname = 'Pecsallée 4'
        new_geom = Point(x=8, y=10, srid=4326)
        features.append({'address': new_streetname,
                         'geom': new_geom.geojson,
                         })

        data = feature_collection['results']
        response = self.client.post(url_locations, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        response = self.client.get(url_locations)
        new_ids = [feature['id'] for feature in
                   response.data['results']['features']]

        url_locations_detail = self.get_location_url(cs, keyflow,
                                                     location=new_ids[1],
                                                     actor=actor.pk)

        # get the new location and check the coordinates and the street
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['address'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_geom.x, new_geom.y]

        # patch a geometry in EWKT format directly in the locations table
        new_geom_ewkt = 'SRID=4326;POINT(6 5)'
        data = {'geom': new_geom_ewkt}
        response = self.client.patch(url_locations_detail, data)
        assert response.status_code == status.HTTP_200_OK

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
        url_locations_detail = self.get_location_url(cs, keyflow,
                                                     location=new_id,
                                                     actor=actor.pk)

        response = self.client.get(url_locations_detail)
        assert response.status_code == status.HTTP_200_OK
        geom = response.data['geometry']
        self.assertJSONEqual(str(geom), new_geom.geojson)
        assert response.data['properties']['address'] == new_streetname

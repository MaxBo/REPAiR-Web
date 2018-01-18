# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.gis.geos.point import Point
from django.urls import reverse
from test_plus import APITestCase
from rest_framework import status
from repair.tests.test import BasicModelTest, LoginTestCase
from rest_framework import status
from repair.apps.login.models import CaseStudy


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

    fixtures = ['auth', 'sandbox']

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
    keyflow = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cs_url = cls.baseurl + reverse('casestudy-detail',
                                           kwargs=dict(pk=cls.casestudy))
        cls.keyflow_url = cls.baseurl + reverse('keyflow-detail',
                                                 kwargs=dict(pk=cls.keyflow))
        cls.url_key = "keyflow"
        cls.url_pks = dict()
        cls.url_pk = dict(pk=1)
        cls.post_data = dict(name='posttestname',
                             casestudies=[cls.cs_url], code='Food')
        cls.put_data = dict(name='puttestname',
                            casestudies=[cls.cs_url],
                            code='Food')
        cls.patch_data = dict(name='patchtestname')

    def setUp(self):
        super().setUp()
        self.obj = KeyflowFactory()


class KeyflowInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 17
    keyflow = 3
    sub_urls = [
    "activitygroups",
    "activities",
    "actors",
    "administrative_locations",
    "operational_locations",
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cs_url = cls.baseurl + reverse('casestudy-detail',
                                   kwargs=dict(pk=cls.casestudy))
        cls.keyflow_url = cls.baseurl + reverse('keyflow-detail',
                                                 kwargs=dict(pk=cls.keyflow))


        cls.url_key = "keyflowincasestudy"
        cls.url_pks = dict(casestudy_pk=cls.casestudy)
        cls.url_pk = dict(pk=cls.keyflow)

        cls.put_data = dict(note='new_put_note',
                             keyflow=cls.keyflow_url,
                             )
        cls.post_data = dict(note='new_note',
                             keyflow=cls.keyflow_url,
                             )

        cls.patch_data = dict(note='patchtestnote')

    def setUp(self):
        super().setUp()
        self.obj = KeyflowInCasestudyFactory(casestudy=self.uic.casestudy,
                                              keyflow__id=self.keyflow)

    def test_post(self):
        url = reverse(self.url_key +'-list', kwargs=self.url_pks)
        # post
        response = self.client.post(url, self.post_data)
        for key in self.post_data:
            assert response.data[key] == self.post_data[key]
        assert response.status_code == status.HTTP_201_CREATED


class Activity2ActivityInMaterialInCaseStudyTest(BasicModelTest, APITestCase):
    """
    MAX:
    1. origin/destination can be in other casestudies than activity2activity
    2. set amount default in model to 0
    """
    casestudy = 17
    keyflow = 3
    origin = 20
    destination = 12
    product = 16
    activity2activity = 13
    keyflowincasestudy = 45
    activitygroup = 76
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "activity2activity"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.activity2activity)

        cls.put_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            product=cls.product,
                             )
        cls.post_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            product=cls.product,
                             )
        cls.patch_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            product=cls.product,
                             )
        cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.obj = Activity2ActivityFactory(id=self.activity2activity,
                                            origin__id=self.origin,
                                            origin__activitygroup__keyflow=kic_obj,
                                            destination__id=self.destination,
                                            destination__activitygroup__keyflow=kic_obj,
                                            product__id=self.product,
                                            product__keyflow=kic_obj,
                                            keyflow=kic_obj
                                            )


class Actor2AtcorInMaterialInCaseStudyTest(BasicModelTest, APITestCase):
    casestudy = 17
    keyflow = 3
    origin = 20
    destination = 12
    product = 16
    actor2actor = 13
    keyflowincasestudy = 45
    activitygroup = 76
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "actor2actor"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.actor2actor)

        cls.put_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            product=cls.product,
                             )
        cls.post_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            product=cls.product,
                             )
        cls.patch_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            product=cls.product,
                             )
        cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.obj = Actor2ActorFactory(id=self.actor2actor,
                                      origin__id=self.origin,
                                      origin__activity__activitygroup__keyflow=kic_obj,
                                      destination__id=self.destination,
                                      destination__activity__activitygroup__keyflow=kic_obj,
                                      product__id=self.product,
                                      product__keyflow=kic_obj,
                                      keyflow=kic_obj,
                                      )


class Group2GroupInKeyflowInCaseStudyTest(BasicModelTest, APITestCase):
    casestudy = 17
    keyflow = 3
    origin = 20
    destination = 12
    product = 16
    group2group = 13
    keyflowincasestudy = 45
    activitygroup = 76
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "group2group"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.group2group)

        cls.put_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            product=cls.product,
                             )
        cls.post_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            product=cls.product,
                             )
        cls.patch_data = dict(origin=cls.origin,
                            destination=cls.destination,
                            product=cls.product,
                             )
        cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.obj = Group2GroupFactory(id=self.group2group,
                                      origin__id=self.origin,
                                      origin__keyflow=kic_obj,
                                      destination__id=self.destination,
                                      destination__keyflow=kic_obj,
                                      product__id=self.product,
                                      product__keyflow=kic_obj,
                                      keyflow=kic_obj,
                                      )



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

    #def test_post(self):
        #"""
        #not sure: Matching query does not exist
        #"""
        #pass


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


class ActivitystockInKeyflowInCasestudyTest(BasicModelTest, APITestCase):
    """
    MAX:
    1. set stock.amount default value to 0
    2. post test not working:
        product should not be required (api/docs)
        also not working via the api html post"""
    casestudy = 17
    keyflow = 3
    origin = 20
    product = 16
    activitystock = 13
    keyflowincasestudy = 45
    activitygroup = 76
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "activitystock"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.activitystock)
        cls.put_data = dict(origin=cls.origin,
                            product=cls.product,
                             )
        cls.post_data = dict(origin=cls.origin,
                             product=cls.product,
                             )
        cls.patch_data = dict(origin=cls.origin,
                              product=cls.product,
                             )
        #cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.obj = ActivityStockFactory(id=self.activitystock,
                                        origin__id=self.origin,
                                        origin__activitygroup__id=self.activitygroup,
                                        origin__activitygroup__keyflow=kic_obj,
                                        product__id=self.product,
                                        product__keyflow=kic_obj,
                                        keyflow=kic_obj,
                                        )

    #def test_post(self):
        #"""
        #not working: produvt id required
        #"""
        #pass


class ActorstockInKeyflowInCasestudyTest(BasicModelTest, APITestCase):
    """
    MAX:
    1. set stock.amount default value to 0
    2. post test not working:
        product should not be required (api/docs)
        also not working via the api html post"""
    casestudy = 17
    keyflow = 3
    origin = 20
    product = 16
    actorstock = 13
    keyflowincasestudy = 45
    activitygroup = 76
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "actorstock"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.actorstock)
        cls.put_data = dict(origin=cls.origin,
                            product=cls.product,
                             )
        cls.post_data = dict(origin=cls.origin,
                             product=cls.product,
                             )
        cls.patch_data = dict(origin=cls.origin,
                              product=cls.product,
                             )
        #cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.obj = ActorStockFactory(id=self.actorstock,
                                     origin__id=self.origin,
                                     origin__activity__activitygroup__id=self.activitygroup,
                                     origin__activity__activitygroup__keyflow=kic_obj,
                                     product__id=self.product,
                                     product__keyflow=kic_obj,
                                     keyflow=kic_obj,
                                     )

    #def test_post(self):
        #"""
        #not working: produvt id required
        #"""
        #pass


class GroupstockInKeyflowInCasestudyTest(BasicModelTest, APITestCase):
    """
    MAX:
    1. set stock.amount default value to 0
    2. post test not working:
        product should not be required (api/docs)
        also not working via the api html post"""
    casestudy = 17
    keyflow = 3
    origin = 20
    product = 16
    groupstock = 13
    keyflowincasestudy = 45
    activitygroup = 76
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "groupstock"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.groupstock)
        cls.put_data = dict(origin=cls.origin,
                            product=cls.product,
                             )
        cls.post_data = dict(origin=cls.origin,
                             product=cls.product,
                             )
        cls.patch_data = dict(origin=cls.origin,
                              product=cls.product,
                             )
        #cls.sub_urls = ['keyflow', 'origin_url', 'destination_url']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.obj = GroupStockFactory(id=self.groupstock,
                                     origin__id=self.origin,
                                     origin__keyflow=kic_obj,
                                     product__id=self.product,
                                     product__keyflow=kic_obj,
                                     keyflow=kic_obj,
                                     )



class ProductsInKeyflowInCasestudyTest(BasicModelTest, APITestCase):
    """
    MAX:
        1. Products is not in casestudy/xx/keyflows/xx/
        2. not shure what fractions is
    """
    casestudy = 17
    keyflow = 3
    product = 16
    keyflowincasestudy = 45
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url_key = "product"
        cls.url_pks = dict(casestudy_pk=cls.casestudy,
                           keyflow_pk=cls.keyflowincasestudy)
        cls.url_pk = dict(pk=cls.product)
        cls.put_data = dict(fractions=[])
        cls.post_data = cls.put_data
        cls.patch_data = dict(name="other name")
        cls.sub_urls = ['keyflow']

    def setUp(self):
        super().setUp()
        kic_obj = KeyflowInCasestudyFactory(id=self.keyflowincasestudy,
                                            casestudy=self.uic.casestudy,
                                            keyflow__id=self.keyflow)
        self.obj = ProductFactory(id=self.product,
                                  keyflow=kic_obj,
                                  )


class GeolocationViewTest(LoginTestCase, APITestCase):


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
                                        'keyflow_pk': keyflow,})

        url_locations_detail = reverse(
            'administrativelocation-detail',
            kwargs={'casestudy_pk': cs,
                    'keyflow_pk': keyflow,
                    'pk': location.pk,})
        url_actor = self.get_url_actor(cs, keyflow, actor)

        # list the activity locations and assert that it contains
        # the new one
        response = self.client.get(url_locations)
        assert response.status_code == status.HTTP_200_OK
        assert location.pk in (row['id'] for row in response.data['features'])

        # patch existing administrative location
        new_streetname = 'Hauptstraße 13'
        data = {'properties': {'address': new_streetname},
                'geometry': location.geom.geojson
                }
        response = self.client.patch(url_locations_detail, data, format='json')
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
        data = {'properties': {'address': new_streetname, 'actor': actor.id},
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

        response = self.client.get(url_locations_detail)
        geom = response.data['geometry']
        assert geom['coordinates'] == [100, -11]

    def get_url_actor(self, cs, keyflow, actor):
        url_actor = reverse('actor-detail', kwargs={'casestudy_pk': cs,
                                                    'keyflow_pk': keyflow,
                                                    'pk': actor.pk,})
        return url_actor

    @staticmethod
    def get_location_url(cs, keyflow, location):
        url_locations_detail = reverse(
            'operationallocation-detail',
            kwargs={'casestudy_pk': cs,
                    'keyflow_pk': keyflow,
                    'pk': location,})
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
                                        'keyflow_pk': keyflow,})

        url_actor = reverse('actor-detail',
                            kwargs={'casestudy_pk': cs,
                                    'keyflow_pk': keyflow,
                                    'pk': actor.pk,})

        # list the activity locations and assert that it contains
        # the new one
        response = self.client.get(url_locations)
        assert response.status_code == status.HTTP_200_OK
        assert location1.pk in (row['id'] for row in response.data['features'])
        assert location2.pk in (row['id'] for row in response.data['features'])

        # patch location1
        url_locations_detail = self.get_location_url(cs, keyflow,
                                                     location=location1.id)
        new_location = Point(x=2, y=3, srid=4326)
        new_streetname = 'Hauptstraße 13'
        data = {'properties': {'address': new_streetname},
                'geometry': new_location.geojson
                }
        response = self.client.patch(url_locations_detail, data, format='json')
        print(response.status_text)
        assert response.status_code == status.HTTP_200_OK

        # check the new adress of the location1
        response = self.client.get(url_locations_detail)
        properties = response.data['properties']
        assert properties['address'] == new_streetname
        coordinates = response.data['geometry']['coordinates']
        assert coordinates == [new_location.x, new_location.y]

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
        data = {'properties': {'address': new_streetname, 'actor': actor.id},
                'geometry': new_geom.geojson}

        response = self.client.post(url_locations, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        new_oloc_id = response.data['id']

        url_locations_detail = reverse(
            'operationallocation-detail',
            kwargs={'casestudy_pk': cs,
                    'keyflow_pk': keyflow,
                    'pk': new_oloc_id,})

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

        response = self.client.get(url_locations_detail)
        geom = response.data['geometry']
        assert geom['coordinates'] == [6, 5]


class TestLocationsOfActor(LoginTestCase, APITestCase):

    @staticmethod
    def get_adminlocation_url(cs, keyflow, location, actor):
        url_locations_detail = reverse(
            'administrativelocation-detail',
            kwargs={'casestudy_pk': cs,
                    'keyflow_pk': keyflow,
                    'actor_pk': actor,
                    'pk': location,})
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
                                        'actor_pk': actor.pk,})

        url_actor = self.get_url_actor(cs, keyflow, actor)

        # list the activity locations and assert that it contains
        # the new one
        response = self.client.get(url_locations)
        assert response.status_code == status.HTTP_200_OK
        assert location.pk in (row['id'] for row in response.data['features'])

        # update existing administrative location with a patch for actor
        new_streetname = 'Hauptstraße 13'
        data = {'address': new_streetname,
                 'geom': location.geom.geojson,
                 'actor': actor.id,
                 }
        response = self.client.post(url_locations, data, format='json')
        print(response.status_text)
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
        data = {'geom' : new_geom_ewkt}
        response = self.client.patch(url_locations_detail, data)
        assert response.status_code == status.HTTP_200_OK

    def get_url_actor(self, cs, keyflow, actor):
        url_actor = reverse('actor-detail', kwargs={'casestudy_pk': cs,
                                                    'keyflow_pk': keyflow,
                                                    'pk': actor.pk,})
        return url_actor

    @staticmethod
    def get_location_url(cs, keyflow, location, actor):
        url_locations_detail = reverse(
            'operationallocation-detail',
            kwargs={'casestudy_pk': cs,
                    'keyflow_pk': keyflow,
                    'actor_pk': actor,
                    'pk': location,})
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
                                        'actor_pk': actor.pk,})

        url_actor = reverse('actor-detail',
                            kwargs={'casestudy_pk': cs,
                                    'keyflow_pk': keyflow,
                                    'pk': actor.pk,})

        # list the activity locations and assert that it contains
        # the new one
        response = self.client.get(url_locations)
        assert response.status_code == status.HTTP_200_OK
        assert location1.pk in (row['id'] for row in response.data['features'])
        assert location2.pk in (row['id'] for row in response.data['features'])

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
        print(response.status_text)
        assert response.status_code == status.HTTP_201_CREATED
        response = self.client.get(url_locations)
        new_location_ids = [feature['id'] for feature in
            response.data['features']]

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
        data = {'geom' : new_geom_ewkt}
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


class PublicationInCaseStudyTest(BasicModelTest, APITestCase):

    casestudy = 1
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

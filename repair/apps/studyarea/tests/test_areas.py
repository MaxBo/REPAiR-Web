# -*- coding: utf-8 -*-

import json
import geojson
from django.urls import reverse
from django.contrib.gis import geos
from django.core.exceptions import FieldError
from test_plus import APITestCase
from rest_framework import status

import repair.apps.studyarea.models as models
from repair.apps.login.factories import CaseStudyFactory
from repair.tests.test import LoginTestCase, CompareAbsURIMixin


class AreaModels(LoginTestCase, APITestCase):
    @classmethod
    def setUpClass(cls):
        super(AreaModels, cls).setUpClass()
        # create a casestudy
        casestudy = cls.uic.casestudy

        adminlevels = models.AdminLevels.objects
        cls.planet = adminlevels.create(name='Planet',
                                        level=models.World._level,
                                        casestudy=casestudy)
        cls.continent = adminlevels.create(name='Continent',
                                           level=models.Continent._level,
                                           casestudy=casestudy)
        cls.country = adminlevels.create(name='Country',
                                         level=models.Country._level,
                                         casestudy=casestudy)
        cls.land = adminlevels.create(name='Province',
                                      level=models.NUTS1._level,
                                      casestudy=casestudy)


    def test_01_dynamic_models(self):

        world = self.planet.create_area(name='Earth')
        eu = self.continent.create_area(name='EU')
        spain = self.country.create_area(name='ES')
        de = self.country.create_area(name='DE')
        hh = self.land.create_area(name='Hamburg')
        catalunia = self.land.create_area(name='Catalunia')
        castilia = self.land.create_area(name='Castilia')

        eu.parent_area = world
        spain.parent_area = eu
        de.parent_area = eu
        hh.parent_area = de
        castilia.parent_area = spain
        catalunia.parent_area = eu

        eu.save()
        spain.save()
        de.save()
        hh.save()
        castilia.save()
        catalunia.save()

        areas = models.Area.objects.all()
        assert areas.count() == 7

        self.assertSetEqual(set(eu.countries.all()), {spain, de})
        self.assertSetEqual(set(eu.nuts1_areas.all()), {catalunia})
        self.assertSetEqual(set(spain.nuts1_areas.all()), {castilia})

        self.assertEqual(models.Area.objects.get(name='ES').country, spain)


class AdminLevels(LoginTestCase, CompareAbsURIMixin, APITestCase):

    @classmethod
    def setUpClass(cls):
        super(AdminLevels, cls).setUpClass()
        # create a casestudy
        casestudy = cls.uic.casestudy

        planet = models.AdminLevels.objects.create(name='Planet',
                                                   level=models.World._level,
                                                   casestudy=casestudy)
        land = models.AdminLevels.objects.create(name='Bundesland',
                                                 level=models.NUTS1._level,
                                                 casestudy=casestudy)
        kreis = models.AdminLevels.objects.create(name='Kreis',
                                                  level=models.NUTS3._level,
                                                  casestudy=casestudy)
        amt = models.AdminLevels.objects.create(name='Amt',
                                                level=models.LAU1._level,
                                                casestudy=casestudy)
        gemeinde = models.AdminLevels.objects.create(name='Gemeinde',
                                                     level=models.LAU2._level,
                                                     casestudy=casestudy)
        ortsteil = models.AdminLevels.objects.create(
            name='Ortsteil',
            level=models.CityNeighbourhood._level,
            casestudy=casestudy)

        cls.casestudy = casestudy
        cls.kreis = kreis
        cls.gemeinde = gemeinde
        cls.ortsteil = ortsteil

        world = planet.create_area(name='Earth')

        saturn = planet.create_area(code='SATURN')

        hh = models.NUTS1.objects.create(name='Hamburg',
                                         parent_area=world)
        sh = models.NUTS1.objects.create(name='Schleswig-Holstein',
                                         parent_area=world)
        kreis_pi = models.NUTS3.objects.create(
            name='Kreis PI',
            parent_area=sh)
        elmshorn = models.LAU2.objects.create(
            name='Elmshorn',
            parent_area=kreis_pi)
        pinneberg = models.LAU2.objects.create(
            name='Pinneberg',
            parent_area=kreis_pi)
        amt_pinnau = models.LAU1.objects.create(
            name='Amt Pinnau',
            parent_area=kreis_pi)
        ellerbek = models.LAU2.objects.create(
            name='Ellerbek',
            parent_area=amt_pinnau)

        schnelsen = models.CityNeighbourhood.objects.create(
            name='Schnelsen',
            parent_area=hh)
        burgwedel = models.CityNeighbourhood.objects.create(
            name='Burgwedel',
            parent_area=hh)
        egenbuettel = models.CityNeighbourhood.objects.create(
            name='Egenbüttel',
            parent_area=ellerbek)
        langenmoor = models.CityNeighbourhood.objects.create(
            name='Langenmoor',
            parent_area=elmshorn)
        elmshorn_mitte = models.CityNeighbourhood.objects.create(
            name='Elmshorn-Mitte',
            parent_area=elmshorn)

        cls.kreis_pi = kreis_pi
        cls.sh = sh

    @classmethod
    def tearDownClass(cls):
        del cls.casestudy
        del cls.kreis
        del cls.gemeinde
        del cls.ortsteil
        del cls.kreis_pi
        super().tearDownClass()

    def test_invalid_areas(self):
        # try to instanciate the Area directly
        planet = models.AdminLevels.objects.get(name='Planet')
        with self.assertRaises(FieldError):
            jupiter = models.Area.objects.create(name='juputer',
                                                 adminlevel=planet)

        with self.assertRaises(FieldError):
            mars = models.World.objects.create(name='Mars')

    def test_get_levels(self):
        """Test the list of all levels of a casestudy"""

        casestudy = self.casestudy
        kreis = self.kreis

        # define the urls
        response = self.get_check_200('adminlevels-list',
                                      casestudy_pk=casestudy.pk)
        data = response.data
        assert data[2]['name'] == kreis.name
        assert data[2]['level'] == kreis.level

    def test_get_gemeinden_of_casestudy(self):
        """Test the list of all areas of a certain level of a casestudy"""

        casestudy = self.casestudy

        response = self.get_check_200('adminlevels-detail',
                                      casestudy_pk=casestudy.pk,
                                      pk=self.gemeinde.pk)
        assert response.data['name'] == 'Gemeinde'
        level_area = response.data['level']

        # define the urls
        response = self.get_check_200('area-list',
                                      casestudy_pk=casestudy.pk,
                                      level_pk=self.gemeinde.pk)
        data = response.data
        self.assertSetEqual({a['name'] for a in data},
                            {'Pinneberg', 'Elmshorn', 'Ellerbek'})

    def test_get_ortsteile_of_kreis(self):
        """
        Test the list of all ortsteile of a kreis with
        an additional filter
        """
        casestudy = self.casestudy
        # get the admin levels
        response = self.get_check_200('adminlevels-list',
                                      casestudy_pk=casestudy.pk)
        data = response.data

        # define the urls
        response = self.get_check_200('area-list',
                                      casestudy_pk=casestudy.pk,
                                      level_pk=self.ortsteil.pk,
                                      data={'parent_level': models.NUTS3._level,
                                            'parent_id': self.kreis_pi.pk,})

        assert response.status_code == status.HTTP_200_OK
        data = response.data

        self.assertSetEqual({a['name'] for a in data},
                            {'Egenbüttel', 'Langenmoor', 'Elmshorn-Mitte'})

        # test if we can use lookups like name__istartswith
        response = self.get_check_200('area-list',
                                      casestudy_pk=casestudy.pk,
                                      level_pk=self.ortsteil.pk,
                                      data={'parent_level': models.NUTS3._level,
                                            'parent_id': self.kreis_pi.pk,
                                            'name__istartswith': 'e',})

        #this should return all ortsteile starting with an 'E'
        self.assertSetEqual({a['name'] for a in response.data},
                           {'Egenbüttel', 'Elmshorn-Mitte'})

    def test_add_geometry(self):
        """Test adding a geometry to an area"""
        response = self.get_check_200('area-detail',
                                      casestudy_pk=self.casestudy.pk,
                                      level_pk=self.kreis_pi.adminlevel.pk,
                                      pk=self.kreis_pi.pk)
        data = response.data
        self.assertEqual(data['type'], 'Feature')
        properties = data['properties']
        cs_uri = self.reverse('casestudy-detail', pk=self.casestudy.pk)
        level_uri = self.reverse('adminlevels-detail',
                                 casestudy_pk=self.casestudy.pk,
                                 pk=self.kreis_pi.adminlevel.pk)
        self.assertURLEqual(properties['casestudy'], cs_uri)
        self.assertURLEqual(properties['adminlevel'], level_uri)
        assert properties['name'] == self.kreis_pi.name

        # geometry is None
        assert data['geometry'] is None

        # add new Polygon as geometry

        polygon = geos.Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0)),
                               ((4, 4), (4, 6), (6, 6), (6, 4), (4, 4)),
                               srid=4326)

        # and change the name
        new_name = 'Kreis Pinneberg-Elmshorn'
        data = {'geometry': polygon.geojson,
                'properties': {'name': new_name,},}
        response = self.patch('area-detail',
                              casestudy_pk=self.casestudy.pk,
                              level_pk=self.kreis_pi.adminlevel.pk,
                              pk=self.kreis_pi.pk,
                              data=json.dumps(data),
                              extra=dict(content_type='application/json'),
                              )
        self.response_200()
        # test if the new geometry is a multipolygon
        multipolygon = geos.MultiPolygon(polygon)
        self.assertJSONEqual(str(response.data['geometry']),
                                multipolygon.geojson)
        # and that the name has changed
        self.assertEqual(response.data['properties']['name'], new_name)

    def test_add_geometries(self):
        """Test adding features as feature collection"""
        response = self.get_check_200('area-list',
                                      casestudy_pk=self.casestudy.pk,
                                      level_pk=self.kreis.pk)
        num_kreise = len(response.data)

        polygon1 = geos.Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0)))
        polygon2 = geos.Polygon(((4, 4), (4, 6), (6, 6), (6, 4), (4, 4)))
        kreis1 = geojson.Feature(geometry=geojson.loads(polygon1.geojson),
                                 properties={'name': 'Kreis1',
                                             'code': '01001',})
        kreis2 = geojson.Feature(geometry=geojson.loads(polygon2.geojson),
                                 properties={'name': 'Kreis2',
                                             'code': '01002',
                                             'parent_area': self.sh.code,})
        kreise = geojson.FeatureCollection([kreis1, kreis2])
        kreise['parent_level'] = str(models.NUTS1._level)
        self.post('area-list',
                  casestudy_pk=self.casestudy.pk,
                  level_pk=self.kreis.pk,
                  data=kreise,
                  extra=dict(content_type='application/json'),
                  )
        self.response_201()
        k2 = models.Area.objects.get(code='01002')
        k1 = models.Area.objects.get(code='01001')
        assert k2.name == 'Kreis2'
        assert k1.name == 'Kreis1'

        k2 = models.NUTS3.objects.get(code='01002')
        assert k2.name == 'Kreis2'
        assert k2.parent_area == self.sh.area_ptr

        response = self.get_check_200('area-list',
                                      casestudy_pk=self.casestudy.pk,
                                      level_pk=self.kreis.pk)
        assert len(response.data) == num_kreise + 2


    def test_add_geometry_with_parent_area(self):
        """Test adding/updating features with parent levels"""
        polygon1 = geos.Polygon(((0, 0), (0, 10), (10, 10), (0, 10), (0, 0)))
        polygon2 = geos.Polygon(((4, 4), (4, 6), (6, 6), (6, 4), (4, 4)))
        kreis1 = geojson.Feature(geometry=geojson.loads(polygon1.geojson),
                                     properties={'name': 'Kreis1',
                                                 'code': '01001',})
        kreis2 = geojson.Feature(geometry=geojson.loads(polygon1.geojson),
                                     properties={'name': 'Kreis2',
                                                     'code': '01002',})
        gem1 = geojson.Feature(geometry=geojson.loads(polygon2.geojson),
                               properties={'name': 'Gemeinde1',
                                           'code': '01002001',
                                           'parent_area': '01002',})
        gem2 = geojson.Feature(geometry=geojson.loads(polygon2.geojson),
                               properties={'name': 'Gemeinde2',
                                           'code': '01001002',
                                           'parent_area': '01001',})
        kreise = geojson.FeatureCollection([kreis1, kreis2])
        self.post('area-list',
                      casestudy_pk=self.casestudy.pk,
                      level_pk=self.kreis.pk,
                      data=kreise,
                      extra=dict(content_type='application/json'),
                      )
        self.response_201()

        gemeinden = geojson.FeatureCollection([gem1, gem2])
        gemeinden['parent_level'] = models.NUTS3._level
        self.post('area-list',
                      casestudy_pk=self.casestudy.pk,
                          level_pk=self.gemeinde.pk,
                          data=gemeinden,
                          extra=dict(content_type='application/json',),
                          )
        self.response_201()

        gem1 = models.LAU2.objects.get(code='01002001')
        assert gem1.parent_area.code == '01002'
        gem2 = models.LAU2.objects.get(code='01001002')
        assert gem2.parent_area.code == '01001'







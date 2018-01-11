# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.gis import geos
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from repair.tests.test import LoginTestCase
from repair.apps.login.factories import (CaseStudyFactory,
                                         UserInCasestudyFactory,
                                         )


class TestCasestudyGeom(LoginTestCase):

    def test_set_get_polygon(self):
        """Test setting and getting geometries from a casestudy"""
        # create a casestudy
        casestudy = self.uic.casestudy

        # define the urls
        url = reverse('casestudy-detail',
                            kwargs={'pk': casestudy.pk,})

        # put polygon as geometry
        polygon = geos.Polygon([
            (2.38, 57.322), (23.194, -20.28), (-120.43, 19.15), (2.38, 57.322)],
            [(-5.21, 23.51), (15.21, -10.81), (-20.51, 1.51), (-5.21, 23.51)])
        data = {'geom': polygon.geojson,}

        response = self.client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        casestudy.refresh_from_db()
        # polygon should have been converted to a multipolygon
        self.assertJSONEqual(casestudy.geom.json,
                             geos.MultiPolygon(polygon).json)

        # send geom as multipolygon and focusarea as polygon
        multipolygon = geos.MultiPolygon(
            polygon,
            geos.Polygon([(3, 3), (4, 4), (5, 3), (3, 3)]))

        data = {'geom': multipolygon.geojson, 'focusarea': polygon.geojson,}

        response = self.client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        casestudy.refresh_from_db()

        # multipolygon should be a multipolygon
        self.assertJSONEqual(casestudy.geom.json,
                             multipolygon.json)
        # polygon for focus area should have been converted to multipolygon
        self.assertJSONEqual(casestudy.focusarea.json,
                             geos.MultiPolygon(polygon).json)


        # get the response
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == casestudy.id
        assert response.data['type'] == 'Feature'
        self.assertJSONEqual(str(response.data['geometry']),
                             multipolygon.json)

        # name and focusarea are stored in as property
        assert response.data['properties']['name'] == casestudy.name
        self.assertJSONEqual(str(response.data['properties']['focusarea']),
                             geos.MultiPolygon(polygon).json)




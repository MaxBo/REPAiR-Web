# -*- coding: utf-8 -*-



from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

import repair.apps.studyarea.models as models
from repair.apps.login.factories import CaseStudyFactory
from repair.tests.test import LoginTestCase

class AreaModels(LoginTestCase):
    def test_01_dynamic_models(self):
        cs = self.uic.casestudy

        world = models.World.objects.create(name='Earth', casestudy=cs)
        eu = models.Continent.objects.create(name='EU', casestudy=cs)
        spain = models.Country.objects.create(name='ES', casestudy=cs)
        de = models.Country.objects.create(name='DE', casestudy=cs)
        hh = models.NUTS1.objects.create(name='Hamburg', casestudy=cs)
        catalunia = models.NUTS1.objects.create(name='Catalunia', casestudy=cs)
        castilia = models.NUTS1.objects.create(name='Castilia', casestudy=cs)

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


class AdminLevels(LoginTestCase):

    @classmethod
    def setUpClass(cls):
        super(AdminLevels, cls).setUpClass()
        # create a casestudy
        casestudy = self.uic.casestudy

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

        world = models.World.objects.create(name='Earth', casestudy=casestudy)
        hh = models.NUTS1.objects.create(name='Hamburg', casestudy=casestudy,
                                         parent_area=world)
        sh = models.NUTS1.objects.create(name='Schleswig-Holstein',
                                         casestudy=casestudy,
                                         parent_area=world)
        kreis_pi = models.NUTS3.objects.create(
            name='Kreis PI', casestudy=casestudy,
            parent_area=sh)
        elmshorn = models.LAU2.objects.create(
            name='Elmshorn', casestudy=casestudy,
            parent_area=kreis_pi)
        pinneberg = models.LAU2.objects.create(
            name='Pinneberg', casestudy=casestudy,
            parent_area=kreis_pi)
        amt_pinnau = models.LAU1.objects.create(
            name='Amt Pinnau', casestudy=casestudy,
            parent_area=kreis_pi)
        ellerbek = models.LAU2.objects.create(
            name='Ellerbek', casestudy=casestudy,
            parent_area=amt_pinnau)

        schnelsen = models.CityNeighbourhood.objects.create(
            name='Schnelsen', casestudy=casestudy,
            parent_area=hh)
        burgwedel = models.CityNeighbourhood.objects.create(
            name='Burgwedel', casestudy=casestudy,
            parent_area=hh)
        egenbuettel = models.CityNeighbourhood.objects.create(
            name='Egenbüttel', casestudy=casestudy,
            parent_area=ellerbek)
        langenmoor = models.CityNeighbourhood.objects.create(
            name='Langenmoor', casestudy=casestudy,
            parent_area=elmshorn)
        elmshorn_mitte = models.CityNeighbourhood.objects.create(
            name='Elmshorn-Mitte', casestudy=casestudy,
            parent_area=elmshorn)

        cls.kreis_pi = kreis_pi


    @classmethod
    def tearDownClass(cls):
        del cls.casestudy
        del cls.kreis
        del cls.gemeinde
        del cls.ortsteil
        del cls.kreis_pi
        super().tearDownClass()


    def test_get_levels(self):
        """Test the list of all levels of a casestudy"""

        casestudy = self.casestudy
        kreis = self.kreis

        # define the urls
        url = reverse('adminlevels-list',
                      kwargs={'casestudy_pk': casestudy.pk,})

        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data[2]['name'] == kreis.name
        assert data[2]['level'] == kreis.level

    def test_get_gemeinden_of_casestudy(self):
        """Test the list of all areas of a casestudy"""

        casestudy = self.casestudy

        url = reverse('adminlevels-detail',
                      kwargs={'casestudy_pk': casestudy.pk,
                              'pk': self.gemeinde.pk,})
        response = self.client.get(url)
        assert response.data['name'] == 'Gemeinde'


        # define the urls
        kwargs = {'casestudy_pk': casestudy.pk,
                  'level_pk': self.gemeinde.level,}
        url = reverse('area-list', kwargs=kwargs, )
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
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
        url = reverse('adminlevels-list',
                          kwargs={'casestudy_pk': casestudy.pk,})
        data = self.client.get(url).data

        # define the urls
        kwargs = {'casestudy_pk': casestudy.pk,
                  'level_pk': self.ortsteil.level,}
        url = reverse('area-list', kwargs=kwargs, )
        response = self.client.get(url, {'parent_level': models.NUTS3._level,
                                         'parent_id': self.kreis_pi.pk,})

        assert response.status_code == status.HTTP_200_OK
        data = response.data

        self.assertSetEqual({a['name'] for a in data},
                            {'Egenbüttel', 'Langenmoor', 'Elmshorn-Mitte'})

        # test if we can use lookups like name__istartswith
        response = self.client.get(url, {'parent_level': models.NUTS3._level,
                                         'parent_id': self.kreis_pi.pk,
                                         'name__istartswith': 'e',})

        #assert response.status_code == status.HTTP_200_OK
        # this should return all ortsteile starting with an 'E'
        #self.assertSetEqual({a['name'] for a in response.data},
        #                    {'Egenbüttel', 'Elmshorn-Mitte'})



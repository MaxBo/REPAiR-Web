from django.test import TestCase
import repair.apps.studyarea.models as models


class AreaModels(TestCase):
    def test_01_dynamic_models(self):
        world = models.World.objects.create(name='Earth')
        eu = models.Continent.objects.create(name='EU')
        spain = models.Country.objects.create(name='ES')
        de = models.Country.objects.create(name='DE')
        hh = models.NUTS1.objects.create(name='Hamburg')
        catalunia = models.NUTS1.objects.create(name='Catalunia')
        castilia = models.NUTS1.objects.create(name='Castilia')

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

        print(areas)
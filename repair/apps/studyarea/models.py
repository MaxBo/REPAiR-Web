from django.db import models
from django.contrib.gis.db import models as geomodels
from django.contrib.contenttypes.models import ContentType

from repair.apps.login.models import GDSEUniqueNameModel, CaseStudy


class StakeholderCategory(GDSEUniqueNameModel):
    casestudy = models.ForeignKey(CaseStudy)
    name = models.TextField()


class Stakeholder(GDSEUniqueNameModel):
    stakeholder_category = models.ForeignKey(StakeholderCategory)
    name = models.TextField()

    @property
    def casestudy(self):
        return self.stakeholder_category.casestudy


class AdminLevels(GDSEUniqueNameModel):
    """Administrative levels to be defined for a casestudy"""
    name = models.TextField()
    level = models.IntegerField()
    casestudy = models.ForeignKey(CaseStudy)

    class Meta:
        unique_together = (('casestudy', 'level',),
                           ('casestudy', 'name',),
                           )


class Area(GDSEUniqueNameModel):
    level = models.ForeignKey(AdminLevels)
    content_type = models.ForeignKey(ContentType)
    name = models.TextField()
    geom = geomodels.MultiPolygonField(null=True, blank=True)
    casestudy = models.ForeignKey(CaseStudy)

    def save(self, *args, **kwargs):
        if self.content_type_id is None:
            content_type = ContentType.objects.get_for_model(self.__class__)
            self.level = content_type.model_class()._level
            self.content_type = content_type
        super().save(*args, **kwargs)


class World(Area):
    """TopLevel"""
    _level = 1


class Continent(Area):
    """TopLevel"""
    _level = 2
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='continents')


class Country(Area):
    """TopLevel"""
    _level = 3
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='countries')


class NUTS1(Area):
    """TopLevel"""
    _level = 4
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='nuts1_areas')


class NUTS2(Area):
    """TopLevel"""
    _level = 5
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='nuts2_areas')


class NUTS3(Area):
    """TopLevel"""
    _level = 6
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='nuts3_areas')


class LAU1(Area):
    """TopLevel"""
    _level = 7
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='lau1_areas')


class LAU2(Area):
    """TopLevel"""
    _level = 8
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='lau2_areas')


class CityDistrict(Area):
    """TopLevel"""
    _level = 9
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='citydistricts')


class CityNeighbourhood(Area):
    """TopLevel"""
    _level = 10
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='neighbourhoods')


class CityBlock(Area):
    """TopLevel"""
    _level = 11
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='blocks')


class StreetSection(Area):
    """TopLevel"""
    _level = 12
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='streetsections')


class House(Area):
    """TopLevel"""
    _level = 13
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='houses')



class Nodes(models.Model):
    #node_id = models.IntegerField(primary_key=True)
    location = models.CharField(max_length=255)
    x_coord = models.FloatField()
    y_coord = models.FloatField()


class Links(models.Model):
    #link_id = models.IntegerField(primary_key=True)
    id_from = models.CharField(max_length=255)
    id_to = models.CharField(max_length=255)
    #link_description = models.CharField(max_length=100)
    weight = models.FloatField()


class Person(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)


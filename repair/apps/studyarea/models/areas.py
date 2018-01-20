
from django.db import models
from django.contrib.gis.db import models as geomodels
from django.contrib.contenttypes.models import ContentType

from repair.apps.login.models import GDSEUniqueNameModel, CaseStudy, GDSEModel


class AdminLevels(GDSEUniqueNameModel):
    """Administrative levels to be defined for a casestudy"""
    name = models.TextField()
    level = models.IntegerField()
    casestudy = models.ForeignKey(CaseStudy)

    class Meta:
        unique_together = (('casestudy', 'level',),
                           ('casestudy', 'name',),
                           )

    def create_area(self, **kwargs):
        """Create an area of the according level"""
        area_model = Areas.by_level[self.level]
        area = area_model.objects.create(adminlevel=self, **kwargs)
        return area


class Area(GDSEModel):
    _unique_field = 'code'
    _submodels = {}

    adminlevel = models.ForeignKey(AdminLevels)
    content_type = models.ForeignKey(ContentType)
    name = models.TextField(null=True, blank=True)
    code = models.TextField()
    geom = geomodels.MultiPolygonField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # use name as code, if code not provided
        if not self.code:
            self.code = self.name

        if self.content_type_id is None:
            adminlevel = None
            try:
                adminlevel = self.adminlevel
                level = adminlevel.level
                area_class = Areas.by_level[level]
                content_type = ContentType.objects.get_for_model(area_class)
            except AdminLevels.DoesNotExist:
                content_type = ContentType.objects.get_for_model(self.__class__)
                level = content_type.model_class()._level

            if not adminlevel:
                # casestudy from the parent_area
                casestudy = self.parent_area.adminlevel.casestudy
                self.adminlevel = AdminLevels.objects.get(level=level,
                                                          casestudy=casestudy,
                                                          )
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


class _AreaTypesMeta(type):
    def __init__(cls, name, bases, nmspc):
        """"""
        super().__init__(name, bases, nmspc)
        for k, v in globals().items():
            if isinstance(v, type) and issubclass(v, Area) and hasattr(v, '_level'):
                cls.by_level[v._level] = v


class Areas(metaclass=_AreaTypesMeta):
    """"""
    by_level = {}

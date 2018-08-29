from django.core.exceptions import FieldError
from django.db import models
from django.contrib.gis.db import models as geomodels

from repair.apps.login.models import GDSEUniqueNameModel, CaseStudy, GDSEModel
from repair.apps.utils.protect_cascade import PROTECT_CASCADE

class AdminLevels(GDSEUniqueNameModel):
    """Administrative levels to be defined for a casestudy"""
    name = models.TextField()
    level = models.IntegerField()
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)

    class Meta(GDSEUniqueNameModel.Meta):
        unique_together = (('casestudy', 'level',),
                           ('casestudy', 'name',),
                           )
        abstract = False

    def create_area(self, **kwargs):
        """Create an area of the according level"""
        area = Area.objects.create(adminlevel=self, **kwargs)
        return area


class Area(GDSEModel):
    _unique_field = 'code'

    adminlevel = models.ForeignKey(AdminLevels, on_delete=PROTECT_CASCADE)
    name = models.TextField(null=True, blank=True)
    code = models.TextField()
    geom = geomodels.MultiPolygonField(null=True, blank=True)
    _parent_area = models.ForeignKey("self", null=True, blank=True,
                                     on_delete=models.CASCADE)

    #def save(self, *args, **kwargs):
        #if not hasattr(self, '_level') and not self.pk:
            #raise FieldError('model {} cannot be created directly. '
                             #'Please create a submodel with a level attribute!')
        ## use name as code, if code not provided
        #if not self.code:
            #self.code = self.name
        #try:
            #adminlevel = self.adminlevel
        #except AdminLevels.DoesNotExist:
                #level = self._level
                ## casestudy from the parent_area
                #try:

                    #casestudy = self.parent_area.adminlevel.casestudy
                #except AttributeError:
                    #raise FieldError('you have to provide the adminlevel'
                                     #' or the parent_area')
                #self.adminlevel = AdminLevels.objects.get(level=level,
                                                          #casestudy=casestudy,
                                                          #)

        #super().save(*args, **kwargs)


class World(Area):
    """TopLevel"""
    _level = 1


class Continent(Area):
    """TopLevel"""
    _level = 2
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='continents'
                                    , on_delete=models.CASCADE)


class Country(Area):
    """TopLevel"""
    _level = 3
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='countries'
                                    , on_delete=models.CASCADE)


class NUTS1(Area):
    """TopLevel"""
    _level = 4
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='nuts1_areas'
                                    , on_delete=models.CASCADE)


class NUTS2(Area):
    """TopLevel"""
    _level = 5
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='nuts2_areas'
                                    , on_delete=models.CASCADE)


class NUTS3(Area):
    """TopLevel"""
    _level = 6
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='nuts3_areas'
                                    , on_delete=models.CASCADE)


class District(Area):
    """TopLevel"""
    _level = 7
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='district_areas'
                                    , on_delete=models.CASCADE)


class Municipality(Area):
    """TopLevel"""
    _level = 8
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='municipality_areas'
                                    , on_delete=models.CASCADE)


class CityDistrict(Area):
    """TopLevel"""
    _level = 9
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='citydistricts'
                                    , on_delete=models.CASCADE)


class CityNeighbourhood(Area):
    """TopLevel"""
    _level = 10
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='neighbourhoods'
                                    , on_delete=models.CASCADE)


class CityBlock(Area):
    """TopLevel"""
    _level = 11
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='blocks'
                                    , on_delete=models.CASCADE)


class StreetSection(Area):
    """TopLevel"""
    _level = 12
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='streetsections'
                                    , on_delete=models.CASCADE)


class House(Area):
    """TopLevel"""
    _level = 13
    parent_area = models.ForeignKey("Area", null=True, blank=True,
                                    related_name='houses'
                                    , on_delete=models.CASCADE)


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

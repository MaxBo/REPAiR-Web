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



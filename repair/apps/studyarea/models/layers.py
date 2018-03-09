from django.db import models

from repair.apps.login.models import GDSEUniqueNameModel, CaseStudy, GDSEModel
from wms_client.models import WMSLayer


class LayerCategory(GDSEUniqueNameModel):
    """Layer Category"""
    name = models.TextField()
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)


class Layer(GDSEModel):
    """"""
    category = models.ForeignKey(LayerCategory, on_delete=models.CASCADE)
    name = models.TextField()
    included = models.BooleanField(default=False)
    z_index = models.IntegerField(default=1)
    wms_layer = models.ForeignKey(WMSLayer, on_delete=models.CASCADE)
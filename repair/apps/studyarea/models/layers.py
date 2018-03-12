from django.db import models

from repair.apps.login.models import GDSEUniqueNameModel, CaseStudy, GDSEModel
from wms_client.models import WMSLayer, LayerStyle


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
    style = models.ForeignKey(LayerStyle, on_delete=models.SET_NULL, null=True)
    
    @property
    def legend_uri(self):
        try:
            style = (self.style if self.style is not None else
                     self.wms_layer.layerstyle_set.get(name='default'))
        except LayerStyle.DoesNotExist:
            return None
        return style.legend_uri
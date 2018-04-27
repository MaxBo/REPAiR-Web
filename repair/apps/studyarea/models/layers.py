from django.db import models

from repair.apps.login.models import GDSEUniqueNameModel, CaseStudy, GDSEModel
from repair.apps.utils.protect_cascade import PROTECT_CASCADE
from wms_client.models import WMSLayer, LayerStyle


class LayerCategory(GDSEUniqueNameModel):
    """Layer Category"""
    name = models.TextField()
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)


class Layer(GDSEModel):
    """"""
    category = models.ForeignKey(LayerCategory, on_delete=PROTECT_CASCADE)
    name = models.TextField()
    included = models.BooleanField(default=False)
    z_index = models.IntegerField(default=1)
    wms_layer = models.ForeignKey(WMSLayer, on_delete=PROTECT_CASCADE)
    style = models.ForeignKey(LayerStyle, on_delete=models.SET_NULL, null=True)

    @property
    def legend_uri(self):
        style_set = self.wms_layer.layerstyle_set
        try:
            # try to take default style
            style = (self.style if self.style is not None else
                     style_set.get(name='default'))
        except LayerStyle.DoesNotExist:
            # try to take first style if no default style is defined
            if len(style_set.all()) > 0:
                style = style_set.first()
            else:
                return None
        return style.legend_uri
import factory
from factory.django import DjangoModelFactory
from repair.apps.login.factories import (CaseStudyFactory)

from . import models
from wms_client.models import WMSLayer, LayerStyle


class WMSResourceFactory(DjangoModelFactory):
    name = 'WMSResource1'
    uri = 'https://monitor.ioer.de/cgi-bin/wms?MAP=O06RG_wms'
    description = 'A short Description'
    preview = ''
    zoom = 15
    min_zoom = 13
    max_zoom = 17
    north = 52.2
    east = 6.7
    west = 7.8
    south = 50.1
    username = 'User1'
    password = 'superpassword'

    class Meta:
        model = models.WMSResource


class WMSResourceInCasestudyFactory(DjangoModelFactory):
    casestudy = factory.SubFactory(CaseStudyFactory)
    wmsresource = factory.SubFactory(WMSResourceFactory)

    class Meta:
        model = models.WMSResourceInCasestudy
        django_get_or_create = ('wmsresource', )


class WMSLayerFactory(DjangoModelFactory):
    wmsresource = factory.SubFactory(WMSResourceFactory)
    name = 'First Layer'
    title = 'Layer No. 1'

    class Meta:
        model = WMSLayer


class LayerStyleFactory(DjangoModelFactory):
    wmslayer = factory.SubFactory(WMSLayerFactory)
    name = 'Style1'
    title = 'A fancy style'
    legend_uri = 'https://example.com/legend'

    class Meta:
        model = LayerStyle

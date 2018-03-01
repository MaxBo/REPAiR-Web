import factory
from factory.django import DjangoModelFactory
from repair.apps.login.factories import (CaseStudyFactory)

from . import models


class WMSResourceFactory(DjangoModelFactory):
    name = 'WMSResource1'
    uri = 'https://example.com'
    layers = 'first_layer,second_layer'
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
    passwort = 'superpassword'

    class Meta:
        model = models.WMSResource


class PublicationInCasestudyFactory(DjangoModelFactory):
    casestudy = factory.SubFactory(CaseStudyFactory)
    wmsresource = factory.SubFactory(WMSResourceFactory)

    class Meta:
        model = models.WMSResourceInCasestudy
        django_get_or_create = ('wmsresource', )

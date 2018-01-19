import factory
from factory.django import DjangoModelFactory
from repair.apps.login.factories import (CaseStudyFactory)

from . import models


class PublicationTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.PublicationType
    title = 'Article'
    description = 'An Article'
    bibtex_types = 'article'


class PublicationFactory(DjangoModelFactory):
    class Meta:
        model = models.Publication
    type = factory.SubFactory(PublicationTypeFactory)
    citekey = 'Wandl.2017'
    title = 'Repair'
    authors = 'Wandl'
    year = 2017
    doi = '10.1000/182'


class PublicationInCasestudyFactory(DjangoModelFactory):
    casestudy = factory.SubFactory(CaseStudyFactory)
    publication = factory.SubFactory(PublicationFactory)

    class Meta:
        model = models.PublicationInCasestudy
        django_get_or_create = ('publication', )

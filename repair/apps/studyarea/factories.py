import factory
from factory.django import DjangoModelFactory
from repair.apps.login.factories import CaseStudyFactory

from . import models


class StakeholderCategoryFactory(DjangoModelFactory):
    class Meta:
        model = models.StakeholderCategory
    name = 'Goverment'
    casestudy = factory.SubFactory(CaseStudyFactory)


class StakeholderFactory(DjangoModelFactory):
    class Meta:
        model = models.Stakeholder
    name = 'Mayor'
    stakeholder_category = factory.SubFactory(StakeholderCategoryFactory)

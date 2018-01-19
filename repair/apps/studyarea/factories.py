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


class AdminLevelsFactory(DjangoModelFactory):
    class Meta:
        model = models.AdminLevels
    level = 1
    name = 'Galaxy'
    casestudy = factory.SubFactory(CaseStudyFactory)


class AreaFactory(DjangoModelFactory):
    class Meta:
        model = models.Area
    code = '01'
    name = 'Lummerland'
    adminlevel = factory.SubFactory(AdminLevelsFactory)


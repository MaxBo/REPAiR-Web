import factory
from factory.django import DjangoModelFactory
from repair.apps.login.factories import (ProfileFactory,
                                         CaseStudyFactory,
                                         UserInCasestudyFactory)
from . import models

class AimFactory(DjangoModelFactory):
    casestudy = factory.SubFactory(CaseStudyFactory)
    text = 'aim text'

    class Meta:
        model = models.aims.Aim


class ChallengeFactory(DjangoModelFactory):
    casestudy = factory.SubFactory(CaseStudyFactory)
    text = 'aim text'

    class Meta:
        model = models.challenges.Challenge


class SustainabilityFieldFactory(DjangoModelFactory):
    name = 'name Sustainability Field'

    class Meta:
        model = models.targets.SustainabilityField


class TargetValueFactory(DjangoModelFactory):
    text = 'text Target Value'
    number = 20
    factor = 30

    class Meta:
        model = models.targets.TargetValue


class TargetSpatialReferenceFactory(DjangoModelFactory):
    name = 'name target spacila reference'
    text = 'text Target Value'

    class Meta:
        model = models.targets.TargetSpatialReference


class AreaOfProtectionFactory(DjangoModelFactory):
    name = 'name of protection area'
    sustainability_field = factory.SubFactory(SustainabilityFieldFactory)

    class Meta:
        model = models.targets.AreaOfProtection


class ImpactCategoryFactory(DjangoModelFactory):
    name = 'name Impact Category'
    area_of_protection = factory.SubFactory(AreaOfProtectionFactory)
    spatial_differentiation = True

    class Meta:
        model = models.targets.ImpactCategory


class TargetFactory(DjangoModelFactory):
    user = factory.SubFactory(UserInCasestudyFactory)
    aim = factory.SubFactory(AimFactory)
    impact_category = factory.SubFactory(ImpactCategoryFactory)
    target_value = factory.SubFactory(TargetValueFactory)
    spatial_reference = factory.SubFactory(TargetSpatialReferenceFactory)

    class Meta:
        model = models.targets.Target
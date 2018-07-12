import factory
from factory.django import DjangoModelFactory
from repair.apps.login.factories import (ProfileFactory,
                                         CaseStudyFactory,
                                         UserInCasestudyFactory)
from repair.apps.statusquo.models.indicators import (SpatialChoice,
                                                     NodeLevel,
                                                     IndicatorType,
                                                     FlowType,
                                                     FlowIndicator,
                                                     IndicatorFlow,
                                                     )
from repair.apps.asmfa.factories import KeyflowInCasestudyFactory
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


class IndicatorFlowFactory(DjangoModelFactory):
    origin_node_level = 1
    origin_node_ids = None
    destination_node_level = 1
    destination_node_ids = None
    materials = None
    spatial_application = 1
    flow_type = 1

    class Meta:
        model = models.indicators.IndicatorFlow


class FlowIndicatorFactory(DjangoModelFactory):
    name = 'FlowIndicator'
    unit = 'some indication unit'
    description = 'some description'
    indicator_type = 1
    flow_a = factory.SubFactory(IndicatorFlowFactory)
    flow_b = factory.SubFactory(IndicatorFlowFactory)
    keyflow = factory.SubFactory(KeyflowInCasestudyFactory)

    class Meta:
        model = models.FlowIndicator
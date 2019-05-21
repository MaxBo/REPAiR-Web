from django.contrib.gis.geos.point import Point

import factory
from factory.django import DjangoModelFactory
from repair.apps.login.factories import UserInCasestudyFactory, UserFactory
from repair.apps.studyarea.factories import StakeholderFactory
from repair.apps.asmfa.factories import (KeyflowInCasestudyFactory, ActorFactory,
                                         ActivityFactory, MaterialFactory,
                                         ProcessFactory, FractionFlowFactory)
from repair.apps.asmfa.models import StrategyFractionFlow
from . import models


class SolutionCategoryFactory(DjangoModelFactory):
    class Meta:
        model = models.SolutionCategory
    name = 'Financial'
    keyflow = factory.SubFactory(KeyflowInCasestudyFactory)


class SolutionFactory(DjangoModelFactory):
    class Meta:
        model = models.Solution
    name = 'Super Solution'
    solution_category = factory.SubFactory(SolutionCategoryFactory)
    description = 'This is the best Solution'


class ImplementationQuestionFactory(DjangoModelFactory):
    class Meta:
        model = models.ImplementationQuestion
    question = 'How many percent are going to be saved?'
    min_value = 0.1
    max_value = 0.5
    step = 0.2
    is_absolute = False


class SolutionPartFactory(DjangoModelFactory):
    class Meta:
        model = models.SolutionPart
    solution = factory.SubFactory(SolutionFactory)
    implements_new_flow = False
    implementation_flow_origin_activity = factory.SubFactory(ActivityFactory)
    implementation_flow_destination_activity = \
        factory.SubFactory(ActivityFactory)
    implementation_flow_material = factory.SubFactory(MaterialFactory)
    implementation_flow_process = factory.SubFactory(ProcessFactory)
    implementation_flow_spatial_application = 1

    question = factory.SubFactory(ImplementationQuestionFactory)
    a = 0
    b = 1


class StrategyFactory(DjangoModelFactory):
    class Meta:
        model = models.Strategy
    name = factory.Sequence(lambda n: "Strategy #%s" % n)
    user = factory.SubFactory(UserInCasestudyFactory)
    coordinating_stakeholder = factory.SubFactory(StakeholderFactory)
    keyflow = factory.SubFactory(KeyflowInCasestudyFactory)


class StrategyFractionFlowFactory(DjangoModelFactory):
    class Meta:
        model = StrategyFractionFlow
    strategy = factory.SubFactory(StrategyFactory)
    fractionflow = factory.SubFactory(FractionFlowFactory)
    material = factory.SubFactory(MaterialFactory)
    amount = 0.0


class SolutionInStrategyFactory(DjangoModelFactory):
    class Meta:
        model = models.SolutionInStrategy
    solution = factory.SubFactory(SolutionFactory)
    strategy = factory.SubFactory(StrategyFactory)

    @factory.post_generation
    def participants(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of participants were passed in, use them
            for participant in extracted:
                self.participants.add(participant)

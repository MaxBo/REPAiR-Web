from django.contrib.gis.geos.point import Point

import factory
from factory.django import DjangoModelFactory
from repair.apps.login.factories import UserInCasestudyFactory, UserFactory
from repair.apps.studyarea.factories import StakeholderFactory
from repair.apps.asmfa.factories import (KeyflowInCasestudyFactory,
                                         ActivityFactory, MaterialFactory,
                                         ProcessFactory)

from . import models


class SolutionCategoryFactory(DjangoModelFactory):
    class Meta:
        model = models.SolutionCategory
    name = 'Financial'
    user = factory.SubFactory(UserInCasestudyFactory)
    keyflow = factory.SubFactory(KeyflowInCasestudyFactory)


class SolutionFactory(DjangoModelFactory):
    class Meta:
        model = models.Solution
    name = 'Super Solution'
    solution_category = factory.SubFactory(SolutionCategoryFactory)
    user = factory.SubFactory(UserInCasestudyFactory)
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
    name = 'Number of Collectors'
    solution = factory.SubFactory(SolutionFactory)
    implements_new_flow = False
    implementation_flow_origin = factory.SubFactory(ActivityFactory)
    implementation_flow_destination = factory.SubFactory(ActivityFactory)
    implementation_flow_material = factory.SubFactory(MaterialFactory)
    implementation_flow_process = factory.SubFactory(ProcessFactory)
    implementation_flow_spatial_application = 0

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

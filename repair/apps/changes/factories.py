from django.contrib.gis.geos.point import Point

import factory
from factory.django import DjangoModelFactory
from repair.apps.login.factories import UserInCasestudyFactory, UserFactory
from repair.apps.studyarea.factories import StakeholderFactory
from repair.apps.asmfa.factories import KeyflowInCasestudyFactory

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
    one_unit_equals = 'One Unit'


class SolutionQuantityFactory(DjangoModelFactory):
    class Meta:
        model = models.SolutionQuantity
    name = 'Number of Collectors'
    solution = factory.SubFactory(SolutionFactory)
    unit = factory.SubFactory(UnitFactory)


class SolutionRatioOneUnitFactory(DjangoModelFactory):
    class Meta:
        model = models.SolutionRatioOneUnit
    solution = factory.SubFactory(SolutionFactory)
    name = 'tons'
    value = 42
    unit = factory.SubFactory(UnitFactory)


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


class StrategyWithOneSolutionFactory(StrategyFactory):
    membership = factory.RelatedFactory(SolutionInStrategyFactory,
                                        'solution')


class StrategyWithTwoSolutionsFactory(UserFactory):
    membership1 = factory.RelatedFactory(SolutionInStrategyFactory,
                                        'solution', solution__name='MySolution1')
    membership2 = factory.RelatedFactory(SolutionInStrategyFactory,
                                        'solution', solution__name='MySolution2')


class SolutionInStrategyQuantityFactory(DjangoModelFactory):
    class Meta:
        model = models.SolutionInStrategyQuantity
    sii = factory.SubFactory(SolutionInStrategyFactory)
    quantity = factory.SubFactory(SolutionQuantityFactory)
    value = 24.3

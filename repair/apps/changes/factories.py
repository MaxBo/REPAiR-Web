from django.contrib.gis.geos.point import Point

import factory
from factory.django import DjangoModelFactory
from repair.apps.login.factories import UserInCasestudyFactory, UserFactory
from repair.apps.studyarea.factories import StakeholderFactory

from . import models


class UnitFactory(DjangoModelFactory):
    class Meta:
        model = models.Unit
    name = 'meter'


class SolutionCategoryFactory(DjangoModelFactory):
    class Meta:
        model = models.SolutionCategory
    name = 'Financial'
    user = factory.SubFactory(UserInCasestudyFactory)


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


class ImplementationFactory(DjangoModelFactory):
    class Meta:
        model = models.Strategy
    name = factory.Sequence(lambda n: "Implementation #%s" % n)
    user = factory.SubFactory(UserInCasestudyFactory)
    coordinating_stakeholder = factory.SubFactory(StakeholderFactory)


class SolutionInImplementationFactory(DjangoModelFactory):
    class Meta:
        model = models.SolutionInStrategy
    solution = factory.SubFactory(SolutionFactory)
    implementation = factory.SubFactory(ImplementationFactory)

    @factory.post_generation
    def participants(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of participants were passed in, use them
            for participant in extracted:
                self.participants.add(participant)


class ImplementationWithOneSolutionFactory(ImplementationFactory):
    membership = factory.RelatedFactory(SolutionInImplementationFactory,
                                        'solution')


class ImplementationWithTwoSolutionsFactory(UserFactory):
    membership1 = factory.RelatedFactory(SolutionInImplementationFactory,
                                        'solution', solution__name='MySolution1')
    membership2 = factory.RelatedFactory(SolutionInImplementationFactory,
                                        'solution', solution__name='MySolution2')


class SolutionInImplementationQuantityFactory(DjangoModelFactory):
    class Meta:
        model = models.SolutionInStrategyQuantity
    sii = factory.SubFactory(SolutionInImplementationFactory)
    quantity = factory.SubFactory(SolutionQuantityFactory)
    value = 24.3

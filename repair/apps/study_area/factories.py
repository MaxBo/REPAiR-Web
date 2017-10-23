import factory 
from factory.django import DjangoModelFactory

from . import models


class CaseStudyFactory(DjangoModelFactory):
    class Meta:
        model = models.CaseStudy

    name = factory.Sequence(lambda n: "CaseStudy #%s" % n)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = models.User
    name = 'Uschi'

    @factory.post_generation
    def casestudies(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of casestudies were passed in, use them
            for casestudy in extracted:
                self.casestudies.add(casestudy)


class UserInCasestudyFactory(DjangoModelFactory):
    class Meta:
        model = models.UserInCasestudy
    user = factory.SubFactory(UserFactory)
    casestudy = factory.SubFactory(CaseStudyFactory)


class UnitFactory(DjangoModelFactory):
    class Meta:
        model = models.Unit
    name = 'meter'


class StakeholderCategoryFactory(DjangoModelFactory):
    class Meta:
        model = models.StakeholderCategory
    name = 'Goverment'
    case_study = factory.SubFactory(CaseStudyFactory)


class StakeholderFactory(DjangoModelFactory):
    class Meta:
        model = models.Stakeholder
    name = 'Mayor'
    stakeholder_category = factory.SubFactory(StakeholderCategoryFactory)


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
        model = models.Implementation
    name = factory.Sequence(lambda n: "Implementation #%s" % n)
    user = factory.SubFactory(UserInCasestudyFactory)
    coordinating_stakeholder = factory.SubFactory(StakeholderFactory)


class SolutionInImplementationFactory(DjangoModelFactory):
    class Meta:
        model = models.SolutionInImplementation
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


class SolutionInImplementationNoteFactory(DjangoModelFactory):
    class Meta:
        model = models.SolutionInImplementationNote
    sii = factory.SubFactory(SolutionInImplementationFactory)
    note = 'Note1'


class SolutionInImplementationQuantityFactory(DjangoModelFactory):
    class Meta:
        model = models.SolutionInImplementationQuantity
    sii = factory.SubFactory(SolutionInImplementationFactory)
    quantity = factory.SubFactory(SolutionQuantityFactory)
    value = 24.3


class SolutionInImplementationGeometryFactory(DjangoModelFactory):
    class Meta:
        model = models.SolutionInImplementationGeometry
    sii = factory.SubFactory(SolutionInImplementationFactory)
    name = 'Hier'
    geom = 'LatLon'


class StrategyFactory(DjangoModelFactory):
    class Meta:
        model = models.Strategy
    user = factory.SubFactory(UserInCasestudyFactory)
    name = 'Strategy 1'
    coordinator = factory.SubFactory(StakeholderFactory)

    @factory.post_generation
    def implementations(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of implementations were passed in, use them
            for implementation in extracted:
                self.implementations.add(implementation)
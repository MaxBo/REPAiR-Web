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

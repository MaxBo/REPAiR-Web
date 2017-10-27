import factory
from factory.django import DjangoModelFactory

from . import models


class CaseStudyFactory(DjangoModelFactory):
    class Meta:
        model = models.CaseStudy

    name = factory.Sequence(lambda n: "CaseStudy #%s" % n)



class UserFactory(DjangoModelFactory):
    username = factory.Sequence(lambda n: 'User {0}'.format(n))
    email = 'uschi@google.com'

    class Meta:
        model = models.User
        django_get_or_create = ('username', )


class ProfileFactory(DjangoModelFactory):
    class Meta:
        model = models.Profile
        django_get_or_create = ('user', )
    user = factory.SubFactory(UserFactory)

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
    user = factory.SubFactory(ProfileFactory)
    casestudy = factory.SubFactory(CaseStudyFactory)

from django.db.models.signals import post_save
import factory
from factory.django import DjangoModelFactory
from . import models
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission


class CaseStudyFactory(DjangoModelFactory):
    class Meta:
        model = models.CaseStudy

    name = factory.Sequence(lambda n: "CaseStudy #%s" % n)


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group
    name = 'Group1'

class UserFactory(DjangoModelFactory):
    """
    Creates a new ``User`` object.
    Username will be a UserN  with ``N`` being a counter.
    Email will be ``uschi@google.com`` .
    Password will be ``test123`` by default.
    """
    username = factory.Sequence(lambda n: 'User {0}'.format(n))
    email = 'uschi@google.com'

    profile = factory.RelatedFactory(
        'repair.apps.login.factories.ProfileFactory', 'user')

    class Meta:
        model = models.User
        django_get_or_create = ('username', )


    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default _create() to disable the post-save signal."""

        # Note: If the signal was defined
        # with a dispatch_uid, include that in both calls.
        password = kwargs.pop('password', 'test123')
        post_save.disconnect(models.create_profile_for_new_user, models.User)
        user = super(UserFactory, cls)._create(model_class, *args, **kwargs)
        user.set_password(password)
        perms = Permission.objects.all()
        user.user_permissions.set(perms)
        post_save.connect(models.create_profile_for_new_user, models.User)
        return user


class ProfileFactory(DjangoModelFactory):
    class Meta:
        model = models.Profile
        django_get_or_create = ('user', )
    user = factory.SubFactory(UserFactory, profile=None)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default _create() to disable the post-save signal."""
        user = kwargs.get('user')
        if user is not None:
            kwargs['id'] = user.id
        profile = super()._create(model_class, *args, **kwargs)
        return profile


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

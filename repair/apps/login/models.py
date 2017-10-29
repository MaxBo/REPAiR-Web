import repair.settings
from django.db import models
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save


class GDSEModel(models.Model):
    """Base class for the GDSE Models"""

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class GDSEUniqueNameModel(GDSEModel):
    """Base class for the GDSE Models"""

    class Meta:
        abstract = True

    def validate_unique(self, *args, **kwargs):
        super(GDSEUniqueNameModel, self).validate_unique(*args, **kwargs)

        qs = self.__class__._default_manager.filter(
            name=self.name
        )

        if qs.exists():
            for row in qs:
                if row.casestudy == self.casestudy:
                    raise ValidationError('{cl} {n} already exists in casestudy {c}'.format(
                            cl=self.__class__.__name__, n=self.name, c=self.casestudy,))

    def save(self, *args, **kwargs):
        """Call :meth:`full_clean` before saving."""
        if self.pk is None:
            self.full_clean()
        super(GDSEUniqueNameModel, self).save(*args, **kwargs)


class CaseStudy(GDSEModel):
    name = models.TextField()

    @property
    def solution_categories(self):
        """
        look for all solution categories created by the users of the casestudy
        """
        solution_categories = set()
        for uic in self.userincasestudy_set.all():
            for solution_category in uic.solutioncategory_set.all():
                solution_categories.add(solution_category)
        return solution_categories

    @property
    def stakeholder_categories(self):
        """
        look for all stakeholder categories created by the users of the casestudy
        """
        stakeholder_categories = set()
        for uic in self.userincasestudy_set.all():
            for stakeholder_category in uic.stakeholdercategory_set.all():
                stakeholder_categories.add(stakeholder_category)
        return stakeholder_categories

    @property
    def implementations(self):
        """
        look for all stakeholder categories created by the users of the casestudy
        """
        implementations = set()
        for uic in self.userincasestudy_set.all():
            for implementation in uic.implementation_set.all():
                implementations.add(implementation)
        return implementations


class Profile(GDSEModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    casestudies = models.ManyToManyField(CaseStudy, through='UserInCasestudy')

    @property
    def name(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_profile_for_new_user(sender, created, instance, **kwargs):
    if created:
        try:
            instance.profile
        except Profile.DoesNotExist:
            profile = Profile(id=instance.id, user=instance)
            profile.save()
        else:
            print(instance.profile)



class UserInCasestudy(GDSEModel):
    user = models.ForeignKey(Profile)
    casestudy = models.ForeignKey(CaseStudy)

    @property
    def name(self):
        return self.user.name

    def __str__(self):
        text = '{u} ({c})'
        return text.format(u=self.user, c=self.casestudy,)

from django.db import models
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.db.models import signals
from django.contrib.auth.models import User as AuthUser


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


class User(GDSEModel):
    user = models.OneToOneField(AuthUser, on_delete=models.CASCADE)
    casestudies = models.ManyToManyField(CaseStudy, through='UserInCasestudy')



class UserInCasestudy(GDSEModel):
    user = models.ForeignKey(User)
    casestudy = models.ForeignKey(CaseStudy)

    def __str__(self):
        text = '{u} ({c})'
        return text.format(u=self.user, c=self.casestudy,)

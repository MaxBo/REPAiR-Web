
from django.contrib.gis.db import models
from repair.apps.login.models import (GDSEUniqueNameModel,
                                      GDSEModel,
                                      UserInCasestudy)


class Unit(GDSEModel):
    name = models.TextField()


class SolutionCategory(GDSEUniqueNameModel):
    user = models.ForeignKey(UserInCasestudy)
    name = models.TextField()

    @property
    def casestudy(self):
        return self.user.casestudy


class Solution(GDSEUniqueNameModel):
    user = models.ForeignKey(UserInCasestudy)
    solution_category = models.ForeignKey(SolutionCategory)
    name = models.TextField()
    description = models.TextField()
    one_unit_equals = models.TextField()

    @property
    def casestudy(self):
        return self.user.casestudy


class SolutionQuantity(GDSEModel):
    solution = models.ForeignKey(Solution)
    unit = models.ForeignKey(Unit)
    name = models.TextField()

    def __str__(self):
        text = '{n} [{u}]'
        return text.format(n=self.name, u=self.unit,)


class SolutionRatioOneUnit(GDSEModel):
    solution = models.ForeignKey(Solution)
    name = models.TextField()
    value = models.FloatField()
    unit = models.ForeignKey(Unit)

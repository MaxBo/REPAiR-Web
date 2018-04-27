
from django.contrib.gis.db import models
from repair.apps.login.models import (GDSEUniqueNameModel,
                                      GDSEModel,
                                      UserInCasestudy)
from repair.apps.asmfa.models import Activity
from repair.apps.utils.protect_cascade import PROTECT_CASCADE


class Unit(GDSEModel):
    name = models.TextField()


class SolutionCategory(GDSEUniqueNameModel):
    user = models.ForeignKey(UserInCasestudy, on_delete=models.CASCADE)
    name = models.TextField()

    @property
    def casestudy(self):
        return self.user.casestudy


class Solution(GDSEUniqueNameModel):
    user = models.ForeignKey(UserInCasestudy, on_delete=PROTECT_CASCADE)
    solution_category = models.ForeignKey(SolutionCategory,
                                          on_delete=PROTECT_CASCADE)
    name = models.TextField()
    description = models.TextField()
    one_unit_equals = models.TextField()
    currentstate_image = models.ImageField(upload_to='charts', null=True,
                                           blank=True)
    effect_image = models.ImageField(upload_to='charts', null=True,
                                     blank=True)
    activities = models.ManyToManyField(Activity)
    activities_image = models.ImageField(upload_to='charts', null=True,
                                         blank=True)

    @property
    def casestudy(self):
        return self.user.casestudy


class SolutionQuantity(GDSEModel):
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=PROTECT_CASCADE)
    name = models.TextField()

    def __str__(self):
        text = '{n} [{u}]'
        return text.format(n=self.name, u=self.unit,)


class SolutionRatioOneUnit(GDSEModel):
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE)
    name = models.TextField()
    value = models.FloatField()
    unit = models.ForeignKey(Unit, on_delete=PROTECT_CASCADE)

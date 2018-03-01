# -*- coding: utf-8 -*-

from django.db import models
#from __future__ import unicode_literals


from repair.apps.login.models import (UserInCasestudy, CaseStudy, User, GDSEModel)



class Aim(GDSEModel):
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)


class Challenge(GDSEModel):
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)


class SustainabilityField(GDSEModel):
    name = models.CharField(max_length=255)


class AreaOfProtection(GDSEModel):
    name = models.CharField(max_length=255)
    sustainability_field = models.ForeignKey(SustainabilityField,
                                             on_delete=models.CASCADE)

class ImpactCategory(GDSEModel):
    name = models.CharField(max_length=255)
    area_of_protection = models.ForeignKey(AreaOfProtection,
                                           on_delete=models.CASCADE)
    spatial_differentiation = models.BooleanField()


class ImpactCategoryInSustainability(GDSEModel):
    impact_category = models.ForeignKey(ImpactCategory,
                                        on_delete=models.CASCADE)


class TargetSpatialReference(GDSEModel):
    name = models.CharField(max_length=255)
    text = models.CharField(max_length=255)


class TargetValue(GDSEModel):
    text = models.CharField(max_length=255)
    number = models.FloatField()
    factor = models.FloatField()


class Target(GDSEModel):
    user = models.ForeignKey(UserInCasestudy, on_delete=models.CASCADE)
    aim = models.ForeignKey(Aim, on_delete=models.CASCADE)
    impact_category = models.ForeignKey(ImpactCategory,
                                        on_delete=models.CASCADE)
    target_value = models.ForeignKey(TargetValue, on_delete=models.CASCADE)
    spatial_reference = models.ForeignKey(TargetSpatialReference,
                                          on_delete=models.CASCADE)

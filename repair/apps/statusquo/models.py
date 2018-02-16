# -*- coding: utf-8 -*-

from django.db import models
#from __future__ import unicode_literals


from repair.apps.login.models import (CaseStudy, User, GDSEModel)



class Aim(GDSEModel):
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)


class Challenge(GDSEModel):
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)


class IndicatorSustainabilityField(GDSEModel):
    name = models.CharField(max_length=255)


class IndicatorAreaOfProtection(GDSEModel):
    name = models.CharField(max_length=255)
    sustainability_field = models.ForeignKey(IndicatorSustainabilityField,
                                             on_delete=models.CASCADE)

class IndicatorImpactCategory(GDSEModel):
    name = models.CharField(max_length=255)
    area_of_protection = models.ForeignKey(IndicatorAreaOfProtection,
                                           on_delete=models.CASCADE)
    spatial_differentiation = models.BooleanField()


class TargetSpatialReference(GDSEModel):
    name = models.CharField(max_length=255)
    text = models.CharField(max_length=255)


class TargetValue(GDSEModel):
    text = models.CharField(max_length=255)
    number = models.FloatField()
    factor = models.FloatField()


class Target(GDSEModel):
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    aim = models.ForeignKey(Aim, on_delete=models.CASCADE)
    impact_category = models.ForeignKey(IndicatorImpactCategory,
                                        on_delete=models.CASCADE)
    target_value = models.ForeignKey(TargetValue, on_delete=models.CASCADE)
    spatial_reference = models.ForeignKey(TargetSpatialReference,
                                          on_delete=models.CASCADE)

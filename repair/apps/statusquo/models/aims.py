# -*- coding: utf-8 -*-

from django.db import models
from repair.apps.login.models import CaseStudy, GDSEModel, User
from repair.apps.asmfa.models import KeyflowInCasestudy
from repair.apps.utils.protect_cascade import PROTECT_CASCADE


class SustainabilityField(GDSEModel):
    name = models.CharField(max_length=255)


class AreaOfProtection(GDSEModel):
    name = models.CharField(max_length=255)
    sustainability_field = models.ForeignKey(SustainabilityField,
                                             on_delete=PROTECT_CASCADE)


class Aim(GDSEModel):
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    keyflow = models.ForeignKey(KeyflowInCasestudy,
                                on_delete=models.CASCADE,
                                null=True, default=None)
    text = models.CharField(max_length=255)
    priority = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        try:
            return self.text or ''
        except Exception:
            return ''


class UserObjective(GDSEModel):
    aim = models.ForeignKey(Aim, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    priority = models.IntegerField(default=-1)
    target_areas = models.ManyToManyField(AreaOfProtection)

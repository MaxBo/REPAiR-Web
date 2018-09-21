# -*- coding: utf-8 -*-

from django.db import models
from repair.apps.login.models import CaseStudy, GDSEModel
from repair.apps.asmfa.models import KeyflowInCasestudy

class Challenge(GDSEModel):
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    keyflow = models.ForeignKey(KeyflowInCasestudy,
                                on_delete=models.CASCADE,
                                null=True, default=None)
    text = models.CharField(max_length=255)
    priority = models.IntegerField(default=0)

    def __str__(self):
        try:
            return self.text or ''
        except Exception:
            return ''

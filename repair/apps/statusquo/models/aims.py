# -*- coding: utf-8 -*-

from django.db import models
from repair.apps.login.models import (CaseStudy, GDSEModel)


class Aim(GDSEModel):
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    priority = models.IntegerField(default=0)

    def __str__(self):
        try:
            return self.text or ''
        except Exception:
            return ''
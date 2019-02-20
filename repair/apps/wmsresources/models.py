# -*- coding: utf-8 -*-
from django.db import models
from repair.apps.login.models import (CaseStudy, GDSEModel)

from wms_client.models import WMSResource


class WMSResourceInCasestudy(GDSEModel):
    wmsresource = models.ForeignKey(WMSResource, on_delete=models.CASCADE)
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)

    class Meta(GDSEModel.Meta):
        unique_together = ('wmsresource', 'casestudy',)

    def __str__(self):
        return '{} ({})'.format(self.wmsresource, self.casestudy)

    def save(self, *args, **kwargs):
        obj = WMSResourceInCasestudy.objects.filter(
                wmsresource=self.wmsresource,
                casestudy=self.casestudy)
        if not obj:
            super().save(*args, **kwargs)

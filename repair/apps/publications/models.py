# -*- coding: utf-8 -*-
from django.db import models
from repair.apps.login.models import (CaseStudy, GDSEModel)

from publications_bootstrap.models import (Publication,
                                           Type as PublicationType)


class PublicationInCasestudy(GDSEModel):
    publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)

    class Meta(GDSEModel.Meta):
        unique_together = ('publication', 'casestudy',)

    def __str__(self):
        return '{} ({})'.format(self.publication, self.casestudy)

    def save(self, force_insert=False, force_update=False, using=None,
            update_fields=None):
        """don't save again if object is already defined"""
        try:
            obj = PublicationInCasestudy.objects.get(
                publication=self.publication,
                casestudy=self.casestudy,
            )
        except PublicationInCasestudy.DoesNotExist:
            obj = super().save(force_insert=force_insert,
                               force_update=force_update,
                               using=using,
                               update_fields=update_fields)
        return obj

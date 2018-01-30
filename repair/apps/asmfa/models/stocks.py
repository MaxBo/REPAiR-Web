# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from repair.apps.asmfa.models.keyflows import (KeyflowInCasestudy, ProductFraction)
from repair.apps.publications.models import PublicationInCasestudy
from repair.apps.asmfa.models.nodes import (
    ActivityGroup,
    Activity,
    Actor,
)
from repair.apps.login.models.bases import GDSEModel



class Stock(GDSEModel):

    # stocks relate to only one node, also data will be entered by the users
    amount = models.IntegerField(blank=True, default=0)
    keyflow = models.ForeignKey(KeyflowInCasestudy, on_delete=models.CASCADE)
    description = models.TextField(max_length=510, blank=True, null=True)
    year = models.IntegerField(default=2016)
    waste = models.BooleanField(default=False)

    class Meta(GDSEModel.Meta):
        abstract = True


class GroupStock(Stock):

    origin = models.ForeignKey(ActivityGroup, on_delete=models.CASCADE,
                               related_name='stocks')
    publication = models.ForeignKey(PublicationInCasestudy, null=True, on_delete=models.SET_NULL,
                                    related_name='GroupStockData')
    fractions = models.ManyToManyField(ProductFraction)


class ActivityStock(Stock):

    origin = models.ForeignKey(Activity, on_delete=models.CASCADE,
                               related_name='stocks')
    fractions = models.ManyToManyField(ProductFraction)
    publication = models.ForeignKey(PublicationInCasestudy, null=True, on_delete=models.SET_NULL,
                                    related_name='ActivityStockData')


class ActorStock(Stock):

    origin = models.ForeignKey(Actor, on_delete=models.CASCADE,
                               related_name='stocks')
    fractions = models.ManyToManyField(ProductFraction)
    publication = models.ForeignKey(PublicationInCasestudy, null=True, on_delete=models.SET_NULL,
                                    related_name='ActorStockData')

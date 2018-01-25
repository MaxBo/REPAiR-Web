# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from repair.apps.asmfa.models.keyflows import (KeyflowInCasestudy, Product)
from repair.apps.publications.models import PublicationInCasestudy
from repair.apps.asmfa.models.nodes import (
    ActivityGroup,
    Activity,
    Actor,
)


class Flow(models.Model):

    amount = models.PositiveIntegerField(blank=True, default=0)

    keyflow = models.ForeignKey(KeyflowInCasestudy, on_delete=models.CASCADE)
    description = models.TextField(max_length=510, blank=True, null=True)
    year = models.IntegerField(default=2016)

    class Meta:
        abstract = True


class Group2Group(Flow):

    destination = models.ForeignKey(ActivityGroup, on_delete=models.CASCADE,
                                    related_name='inputs')
    origin = models.ForeignKey(ActivityGroup, on_delete=models.CASCADE,
                               related_name='outputs')
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='GroupFlows')
    publication = models.ForeignKey(PublicationInCasestudy, null=True, on_delete=models.SET_NULL,
                                    related_name='Group2GroupData')


class Activity2Activity(Flow):

    destination = models.ForeignKey(Activity, on_delete=models.CASCADE,
                                    related_name='inputs',
                                    )
    origin = models.ForeignKey(Activity, on_delete=models.CASCADE,
                               related_name='outputs',
                               )
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='ActivityFlows')
    publication = models.ForeignKey(PublicationInCasestudy, null=True, on_delete=models.SET_NULL,
                                    related_name='Activity2ActivityData')


class Actor2Actor(Flow):

    destination = models.ForeignKey(Actor, on_delete=models.CASCADE,
                                    related_name='inputs')
    origin = models.ForeignKey(Actor, on_delete=models.CASCADE,
                               related_name='outputs')
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='ActorFlows')
    publication = models.ForeignKey(PublicationInCasestudy, null=True, on_delete=models.SET_NULL,
                                    related_name='Actor2ActorData')
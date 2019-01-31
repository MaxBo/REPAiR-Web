# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from repair.apps.asmfa.models.keyflows import (KeyflowInCasestudy, Composition,
                                               Material, ProductFraction)
from repair.apps.publications.models import PublicationInCasestudy
from repair.apps.asmfa.models.nodes import (
    ActivityGroup,
    Activity,
    Actor,
)
from repair.apps.login.models.bases import GDSEModel
from repair.apps.utils.protect_cascade import PROTECT_CASCADE


class Process(GDSEModel):
    name = models.TextField()


class Flow(GDSEModel):

    amount = models.PositiveIntegerField(blank=True, default=0)

    keyflow = models.ForeignKey(KeyflowInCasestudy, on_delete=models.CASCADE)
    description = models.TextField(max_length=510, blank=True, null=True)
    year = models.IntegerField(default=2016)
    waste = models.BooleanField(default=False)
    process = models.ForeignKey(Process, on_delete=models.SET_NULL, null=True)

    class Meta(GDSEModel.Meta):
        abstract = True


class Group2Group(Flow):

    destination = models.ForeignKey(ActivityGroup,
                                    on_delete=PROTECT_CASCADE,
                                    related_name='inputs')
    origin = models.ForeignKey(ActivityGroup,
                               on_delete=PROTECT_CASCADE,
                               related_name='outputs')
    composition = models.ForeignKey(Composition,
                                    on_delete=models.SET_NULL,
                                    related_name='group2group',
                                    null=True,
                                    )
    publication = models.ForeignKey(PublicationInCasestudy,
                                    null=True,
                                    on_delete=models.SET_NULL,
                                    related_name='Group2GroupData')


class Activity2Activity(Flow):

    destination = models.ForeignKey(Activity,
                                    on_delete=PROTECT_CASCADE,
                                    related_name='inputs',
                                    )
    origin = models.ForeignKey(Activity,
                               on_delete=PROTECT_CASCADE,
                               related_name='outputs',
                               )
    composition = models.ForeignKey(Composition,
                                    on_delete=models.SET_NULL,
                                    related_name='activity2activity',
                                    null=True,
                                    )
    publication = models.ForeignKey(PublicationInCasestudy,
                                    null=True,
                                    on_delete=models.SET_NULL,
                                    related_name='Activity2ActivityData')


class Actor2Actor(Flow):

    destination = models.ForeignKey(Actor,
                                    on_delete=PROTECT_CASCADE,
                                    related_name='inputs')
    origin = models.ForeignKey(Actor,
                               on_delete=PROTECT_CASCADE,
                               related_name='outputs')
    composition = models.ForeignKey(Composition,
                                    on_delete=models.SET_NULL,
                                    related_name='actor2actor',
                                    null=True,
                                    )
    publication = models.ForeignKey(PublicationInCasestudy,
                                    null=True,
                                    on_delete=models.SET_NULL,
                                    related_name='Actor2ActorData')

    def save(self, **kwargs):
        super().save(**kwargs)

        # delete eventually already translated fraction flows
        # (recreation in any case)
        fraction_flows = FractionFlow.objects.filter(flow=self)
        fraction_flows.delete()
        composition = self.composition
        fractions = ProductFraction.objects.filter(composition=composition)
        for fraction in fractions:
            fraction_flow = FractionFlow(
                flow=self,
                origin=self.origin,
                destination=self.destination,
                material=fraction.material,
                amount=self.amount*fraction.fraction,
                nace=composition.nace,
                composition_name=composition.name,
                publication=fraction.publication or self.publication,
                avoidable=fraction.avoidable,
                hazardous=fraction.hazardous,
                waste=self.waste,
                process=self.process,
                keyflow=self.keyflow,
                description=self.description,
                year=self.year
            )
            fraction_flow.save()


class FractionFlow(Flow):
    # fraction flow can be related to a keyflow (status quo)
    # but doesn't have to (modified strategy)
    flow = models.ForeignKey(Actor2Actor,
                             on_delete=models.CASCADE,
                             null=True,
                             related_name='f_flow')
    destination = models.ForeignKey(Actor,
                                    on_delete=PROTECT_CASCADE,
                                    related_name='f_inputs')
    origin = models.ForeignKey(Actor,
                               on_delete=PROTECT_CASCADE,
                               related_name='f_outputs')
    material = models.ForeignKey(Material,
                                 on_delete=PROTECT_CASCADE,
                                 related_name='f_material')

    amount = models.BigIntegerField(default=0) # in kilograms

    nace = models.CharField(max_length=255, blank=True)
    composition_name = models.CharField(max_length=255, blank=True)
    publication = models.ForeignKey(PublicationInCasestudy, null=True,
                                    on_delete=models.SET_NULL,
                                    related_name='f_pub')
    avoidable = models.BooleanField(default=True)
    hazardous = models.BooleanField(default=True)






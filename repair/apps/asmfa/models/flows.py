# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from repair.apps.asmfa.models import (KeyflowInCasestudy, Composition,
                                      Material, ProductFraction,
                                      Process)
from repair.apps.changes.models.strategies import Strategy
from repair.apps.publications.models import PublicationInCasestudy
from repair.apps.asmfa.models.nodes import (
    ActivityGroup,
    Activity,
    Actor
)

from repair.apps.login.models.bases import GDSEModel
from repair.apps.utils.protect_cascade import PROTECT_CASCADE


class Flow(GDSEModel):

    amount = models.BigIntegerField(blank=True, default=0)

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
                stock=None,
                to_stock=False,
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
    composition = models.ForeignKey(Composition, on_delete=models.CASCADE,
                                    related_name='groupstock', null=True)


class ActivityStock(Stock):

    origin = models.ForeignKey(Activity, on_delete=models.CASCADE,
                               related_name='stocks')
    publication = models.ForeignKey(PublicationInCasestudy, null=True, on_delete=models.SET_NULL,
                                    related_name='ActivityStockData')
    composition = models.ForeignKey(Composition, on_delete=models.CASCADE,
                                    related_name='activitystock', null=True)


class ActorStock(Stock):

    origin = models.ForeignKey(Actor, on_delete=models.CASCADE,
                               related_name='stocks')
    publication = models.ForeignKey(PublicationInCasestudy, null=True, on_delete=models.SET_NULL,
                                    related_name='ActorStockData')
    composition = models.ForeignKey(Composition, on_delete=models.CASCADE,
                                    related_name='actorstock', null=True)

    def save(self, **kwargs):
        super().save(**kwargs)

        # delete eventually already translated fraction flows
        # (recreation in any case)
        fraction_flows = FractionFlow.objects.filter(stock=self)
        fraction_flows.delete()
        composition = self.composition
        fractions = ProductFraction.objects.filter(composition=composition)
        for fraction in fractions:
            fraction_flow = FractionFlow(
                flow=None,
                stock=self,
                to_stock=True,
                origin=self.origin,
                destination=None,
                material=fraction.material,
                amount=self.amount*fraction.fraction,
                nace=composition.nace,
                composition_name=composition.name,
                publication=fraction.publication or self.publication,
                avoidable=fraction.avoidable,
                hazardous=fraction.hazardous,
                waste=self.waste,
                process=None,
                keyflow=self.keyflow,
                description=self.description,
                year=self.year
            )
            fraction_flow.save()


class FractionFlow(Flow):
    # fraction flow can be related to a keyflow or stock (status quo)
    # but doesn't have to either of them (modified strategy)
    flow = models.ForeignKey(Actor2Actor,
                             on_delete=models.CASCADE,
                             null=True,
                             related_name='f_flow')
    stock = models.ForeignKey(ActorStock,
                              on_delete=models.CASCADE,
                              null=True,
                              related_name='f_stock')
    # origin can be null in case of solution_part
    origin = models.ForeignKey(Actor,
                               null=True,
                               on_delete=PROTECT_CASCADE,
                               related_name='f_outputs')
    # destinations can be null in case of stocks or solution_part
    destination = models.ForeignKey(Actor,
                                    null=True,
                                    on_delete=PROTECT_CASCADE,
                                    related_name='f_inputs')
    material = models.ForeignKey(Material,
                                 on_delete=PROTECT_CASCADE,
                                 related_name='f_material')
    # fraction flow goes to stock (you could also tell by missing destination,
    # but this way we play it safe)
    to_stock = models.BooleanField(default=False)

    amount = models.FloatField(default=0) # in tons

    publication = models.ForeignKey(PublicationInCasestudy, null=True,
                                    on_delete=models.SET_NULL,
                                    related_name='f_pub')
    avoidable = models.BooleanField(default=True)
    hazardous = models.BooleanField(default=True)

    # composition related information
    nace = models.CharField(max_length=255, blank=True)
    composition_name = models.CharField(max_length=255, blank=True)

    strategy = models.ForeignKey(Strategy, null=True,
                                 on_delete=models.CASCADE,
                                 related_name='f_newfractionflowstrategy')


class StrategyFractionFlow(GDSEModel):
    strategy = models.ForeignKey(Strategy,
                             on_delete=models.CASCADE,
                             related_name='f_fractionflowstrategy')
    fractionflow = models.ForeignKey(FractionFlow,
                                     on_delete=models.CASCADE,
                                     related_name='f_strategyfractionflow')
    amount = models.FloatField(default=0) # in tons
    origin = models.ForeignKey(Actor,
                               null=True,
                               on_delete=models.CASCADE,
                               related_name='f_strategyfractionflowoutputs')
    destination = models.ForeignKey(Actor,
                                    null=True,
                                    on_delete=models.CASCADE,
                                    related_name='f_strategyfractionflowinputs')
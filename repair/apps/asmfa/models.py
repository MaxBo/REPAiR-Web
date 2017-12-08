# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.gis.db import models as gis
from djmoney.models.fields import MoneyField

from repair.apps.login.models import (CaseStudy, Profile,
                                      GDSEModel, get_default)

from django.utils.timezone import now


class DataEntry(GDSEModel):

    user = models.CharField(max_length=255, default="tester")
    source = models.URLField(max_length=255, default="www.osf.io")  # this will be a link to OSF
    date = models.DateTimeField(default=now)
    raw = models.BooleanField(default=True)


class Keyflow(GDSEModel):
    # the former "Material" class - not to confuse with the other one
    keyflow_choices = (("Org", "Organic"),
                       ("CDW", "Construction & Demolition"),
                       ("Food", "Food"),
                       ("MSW", "Municipal Solid Waste"),
                       ("PCPW", "Post-Consumer Plastic"),
                       ("HHW", "Household Hazardous Waste"))
    code = models.TextField(choices=keyflow_choices)
    name = models.TextField()
    casestudies = models.ManyToManyField(CaseStudy,
                                         through='KeyflowInCasestudy')


class KeyflowInCasestudy(models.Model):
    keyflow = models.ForeignKey(Keyflow, on_delete=models.CASCADE,
                                related_name='products')
    casestudy = models.ForeignKey(CaseStudy)
    note = models.TextField(default='', blank=True)


# class Material(GDSEModel):
    # now called Keyflow, not to confuse with the other Material class

    # code = models.TextField(unique=True, default='')
    # name = models.TextField()
    # casestudies = models.ManyToManyField(CaseStudy,
    #                                      through='MaterialInCasestudy')


# class MaterialInCasestudy(models.Model):
    # now called KeyflowInCasestudy

    # material = models.ForeignKey(Material)
    # casestudy = models.ForeignKey(CaseStudy)
    # note = models.TextField(default='', blank=True)


class Product(GDSEModel):

    # not sure about the max length, leaving everywhere 255 for now
    name = models.CharField(max_length=255, null=True)
    default = models.BooleanField(default=True)
    keyflow = models.ForeignKey(KeyflowInCasestudy, on_delete=models.CASCADE,
                                related_name='products')


class Material(GDSEModel):

    # not the same as the former Material class that has been renamed to Keyflow
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    flowType = models.CharField(max_length=255, null=True)


class ProductFraction(models.Model):

    fraction = models.FloatField(default=1)

    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='fractions')
    material = models.ForeignKey(Material, on_delete=models.CASCADE,
                                 related_name='products')


class Quality(GDSEModel):
    # not used anymore

    # material = models.ForeignKey(Material,
                                # on_delete=models.CASCADE)
    # name = models.TextField()
    pass


class Node(GDSEModel):

    # source = models.BooleanField(default=False) # not used anymore
    # sink = models.BooleanField(default=False) # not used anymore

    done = models.BooleanField(default=False)  # if true - data entry is done, no edit allowed

    class Meta:
        abstract = True


class ActivityGroup(Node):

    # activity groups are predefined and same for all flows and case studies
    activity_group_choices = (("P1", "Production"),
                              ("P2", "Production of packaging"),
                              ("P3", "Packaging"),
                              ("D", "Distribution"),
                              ("S", "Selling"),
                              ("C", "Consuming"),
                              ("SC", "Selling and Cosuming"),
                              ("R", "Return Logistics"),
                              ("COL", "Collection"),
                              ("W", "Waste Management"),
                              ("imp", "Import"),  # 'import' and 'export' are "special" types of activity groups/activities/actors
                              ("exp", "Export"))
    code = models.CharField(max_length=10, choices=activity_group_choices)
    name = models.CharField(max_length=255)
    keyflow = models.ForeignKey(KeyflowInCasestudy,
                                on_delete=models.CASCADE)



class Activity(Node):

    nace = models.CharField(max_length=255)  # NACE code, unique for each activity
    name = models.CharField(max_length=255)  # not sure about the max length, leaving everywhere 255 for now

    activitygroup = models.ForeignKey(ActivityGroup,
                                      on_delete=models.CASCADE)


class Actor(Node):

    BvDid = models.CharField(max_length=255) #unique actor identifier in ORBIS database
    name = models.CharField(max_length=255)

    reason_choice = ((0, "Included"),
                     (1, "Outside Region, inside country"),
                     (2, "Outside Region, inside EU"),
                     (3, "Outside Region, outside EU"),
                     (4, "Outside Material Scope"),
                     (5, "Does Not Produce Waste"))
    reason = models.IntegerField(choices=reason_choice, default=0)
    # if false - actor will be ignored
    included = models.BooleanField(default=True)

    # operational_location = models.ForeignKey(
    #     'Geolocation',
    #     on_delete=models.CASCADE,
    #     related_name='operational_location',
    #     null=True)
    # administrative_location = models.ForeignKey(
    #     'Geolocation',
    #     on_delete=models.CASCADE,
    #     related_name='administrative_location',
    #     null=True)

    consCode = models.CharField(max_length=255, blank=True, null=True)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    description_eng = models.TextField(max_length=510, blank=True, null=True)
    description = models.TextField(max_length=510, blank=True, null=True)
    BvDii = models.CharField(max_length=255, blank=True, null=True)
    website = models.URLField(max_length=255, blank=True, null=True)
    employees = models.IntegerField(default=1)
    turnover = MoneyField(max_digits=10, decimal_places=2,
                          default_currency='EUR')

    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)


class Geolocation(gis.Model):

    country_choices = (("NL", "The Netherlands"),
                       ("IT", "Italy"),
                       ("PL", "Poland"),
                       ("DE", "Germany"),
                       ("BE", "Belgium"),
                       ("HU", "Hungary"),
                       ("SB", "Sandbox"),
                       ("EU", "European Union"),
                       ("-1", "Outside EU"))

    name = models.TextField(blank=True, null=True)
    postcode = models.CharField(max_length=10, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, choices=country_choices,
                               default="-1")
    city = models.CharField(max_length=255, blank=True, null=True)
    geom = gis.PointField(blank=True, null=True)

    def __str__(self):
        ret = '{s}@({g})'.format(s=self.address, g=self.geom)
        return ret

    class Meta:
        abstract = True


class Establishment(Geolocation):

    # actor = models.OneToOneField(Actor, default=get_default(Actor))

    @property
    def casestudy(self):
        return self.actor.activity.activitygroup.keyflow.casestudy

    class Meta:
        abstract = True


class AdministrativeLocation(Establishment):
    """Administrative Location of Actor"""
    actor = models.OneToOneField(Actor,
                                 null=True,
                                 #default=get_default(Actor),
                                 related_name='administrative_location')


class OperationalLocation(Establishment):
    """Operational Location of Actor"""
    actor = models.ForeignKey(Actor,
                              #default=get_default(Actor),
                              related_name='operational_locations')


class Flow(models.Model):

    amount = models.PositiveIntegerField(blank=True)
    # called this "keyflow" instead of "material", not to confuse with Material class
    keyflow = models.ForeignKey(KeyflowInCasestudy, on_delete=models.CASCADE)
    # quality = models.ForeignKey(Quality, on_delete=models.CASCADE,
    #                             default=1)
    description = models.TextField(max_length=510, blank=True, null=True)

    class Meta:
        abstract = True


class Group2Group(Flow):

    destination = models.ForeignKey(ActivityGroup, on_delete=models.CASCADE,
                                    related_name='inputs')
    origin = models.ForeignKey(ActivityGroup, on_delete=models.CASCADE,
                               related_name='outputs')
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='GroupFlows')
    entry = models.ForeignKey(DataEntry, on_delete=models.CASCADE,
                              related_name='Group2GroupData', default=1)


class Activity2Activity(Flow):

    destination = models.ForeignKey(Activity, on_delete=models.CASCADE,
                                    related_name='inputs',
                                    )
    origin = models.ForeignKey(Activity, on_delete=models.CASCADE,
                               related_name='outputs',
                               )
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='ActivityFlows')
    entry = models.ForeignKey(DataEntry, on_delete=models.CASCADE,
                              related_name='Activity2ActivityData', default=1)


class Actor2Actor(Flow):

    destination = models.ForeignKey(Actor, on_delete=models.CASCADE,
                                    related_name='inputs')
    origin = models.ForeignKey(Actor, on_delete=models.CASCADE,
                               related_name='outputs')
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='ActorFlows')
    entry = models.ForeignKey(DataEntry, on_delete=models.CASCADE,
                              related_name='Actor2ActorData', default=1)


class Stock(models.Model):

    # stocks relate to only one node, also data will be entered by the users
    amount = models.IntegerField(blank=True)
    keyflow = models.ForeignKey(KeyflowInCasestudy, on_delete=models.CASCADE)
    description = models.TextField(max_length=510, blank=True, null=True)

    # quality = models.ForeignKey(Quality, on_delete=models.CASCADE,
                                    # default=13)

    class Meta:
        abstract = True


class GroupStock(Stock):

        origin = models.ForeignKey(ActivityGroup, on_delete=models.CASCADE,
                                   related_name='stocks')
        product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                    related_name='GroupStocks')
        entry = models.ForeignKey(DataEntry, on_delete=models.CASCADE,
                                  related_name='GroupStockData', default=1)


class ActivityStock(Stock):

        origin = models.ForeignKey(Activity, on_delete=models.CASCADE,
                                   related_name='stocks')
        product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                    related_name='ActivityStocks')
        entry = models.ForeignKey(DataEntry, on_delete=models.CASCADE,
                                  related_name='ActivityStockData', default=1)


class ActorStock(Stock):

        origin = models.ForeignKey(Actor, on_delete=models.CASCADE,
                                   related_name='stocks')
        product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                    related_name='ActorStocks')
        entry = models.ForeignKey(DataEntry, on_delete=models.CASCADE,
                                  related_name='ActorStockData', default=1)

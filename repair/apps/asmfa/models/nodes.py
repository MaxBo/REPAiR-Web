# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from djmoney.models.fields import MoneyField

from repair.apps.login.models import GDSEModel
from .keyflows import KeyflowInCasestudy


class DataEntry(GDSEModel):

    user = models.CharField(max_length=255, default="tester")
    source = models.URLField(max_length=255, default="www.osf.io")  # this will be a link to OSF
    date = models.DateTimeField(default=now)
    raw = models.BooleanField(default=True)


class Node(GDSEModel):

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
                              # 'import' and 'export' are "special" types
                              # of activity groups/activities/actors
                              ("imp", "Import"),
                              ("exp", "Export"))
    code = models.CharField(max_length=10, choices=activity_group_choices)
    name = models.CharField(max_length=255)
    keyflow = models.ForeignKey(KeyflowInCasestudy,
                                on_delete=models.CASCADE)


class Activity(Node):

    # NACE code, unique for each activity
    nace = models.CharField(max_length=255)
    # not sure about the max length, leaving everywhere 255 for now
    name = models.CharField(max_length=255)
    activitygroup = models.ForeignKey(ActivityGroup,
                                      on_delete=models.CASCADE)


class Actor(Node):

    # unique actor identifier in ORBIS database
    BvDid = models.CharField(max_length=255)
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

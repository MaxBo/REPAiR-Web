# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.timezone import now
from djmoney.models.fields import MoneyField

from repair.apps.login.models import GDSEModel
from repair.apps.asmfa.models.keyflows import KeyflowInCasestudy


class Node(GDSEModel):

    done = models.BooleanField(default=False)  # if true - data entry is done, no edit allowed

    class Meta(GDSEModel.Meta):
        abstract = True
        #default_permissions = ('add', 'change', 'delete', 'view')


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

    @property
    def nace_codes(self):
        """
        returns a set of the nace codes of the activities
        that belong to the activity group

        Returns
        -------
        nace_code : set
        """
        return set((act['nace'] for act in self.activity_set.values()))


class Activity(Node):

    # NACE code, unique for each activity
    nace = models.CharField(max_length=255)
    # not sure about the max length, leaving everywhere 255 for now
    name = models.CharField(max_length=255)
    activitygroup = models.ForeignKey(ActivityGroup,
                                      on_delete=models.CASCADE)


class Reason(models.Model):
    """Reason for exclusion of actors"""
    reason = models.TextField()

    def __str__(self):
        return self.reason


class Actor(Node):

    # unique actor identifier in ORBIS database
    BvDid = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

    reason = models.ForeignKey(Reason, null=True, on_delete=models.SET_NULL)
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

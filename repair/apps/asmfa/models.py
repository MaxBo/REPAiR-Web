# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class DataEntry(models.Model):

    # this I am leaving empty for now - we have to agree at the consortium how we define users and data sources
    user = models.CharField(max_length=255, primary_key=True)
    source = models.CharField(max_length=255)
    #date =
    pass


class Geolocation(models.Model):

    # same as for DataEntry, also geometry will have to be included later
    #street =
    #building =
    #postcode =
    #country =
    #city =
    #geom =
    pass


class Node(models.Model):  # should there be a separate model for the AS-MFA?

    # all the data for the Node class tables will be known in advance, the users will not have to fill that in
    source = models.BooleanField(default=False)  # if true - there is no input, should be introduced as a constraint later
    sink = models.BooleanField(default=False)  # if true - there is no output, same

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
    code = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255, choices=activity_group_choices)


class Activity(Node):

    nace = models.CharField(max_length=255, primary_key=True)  # NACE code, unique for each activity
    name = models.CharField(max_length=255)  # not sure about the max length, leaving everywhere 255 for now

    own_activitygroup = models.ForeignKey(ActivityGroup,
                                          on_delete=models.CASCADE,
                                          related_name='Activities',
                                          default=1)


class Actor(Node):

    BvDid = models.CharField(max_length=255, primary_key=True) #unique actor identifier in ORBIS database
    name = models.CharField(max_length=255)

    # locations also let's leave out for now, we can add them later
    #operationalLocation = models.ForeignKey('Geolocation', on_delete=models.CASCADE, related_name='operationalLocation')
    #administrativeLocation = models.ForeignKey('Geolocation', on_delete=models.CASCADE, related_name='administrativeLocation')
    consCode = models.CharField(max_length=255)
    year = models.PositiveSmallIntegerField()
    revenue = models.PositiveIntegerField()
    employees = models.PositiveSmallIntegerField()
    BvDii = models.CharField(max_length=255)
    website = models.CharField(max_length=255)

    own_activity = models.ForeignKey(Activity, on_delete=models.CASCADE,
                                     related_name='Actors',
                                     default=1)


class Flow(models.Model):

    # users will have to add data about flows, that will relate two of the nodes
    # again, there will be limited material and quality choices, we should determine the exact ones later
    material_choices = (("PET", "PET plastic"),
                        ("Org", "Organic"),
                        ("PVC", "PVC plastic"))
    quality_choices = (("1", "High"),
                       ("2", "Medium"),
                       ("3", "Low"),
                       ("4", "Waste"))

    material = models.CharField(max_length=255, choices=material_choices, blank=True)
    amount = models.PositiveIntegerField(blank=True)
    quality = models.CharField(max_length=255, choices=quality_choices, blank=True)

    class Meta:
        abstract = True


class Group2Group(Flow):

    destination = models.ForeignKey(ActivityGroup, on_delete=models.CASCADE,
                                    related_name='Inputs')
    origin = models.ForeignKey(ActivityGroup, on_delete=models.CASCADE,
                               related_name='Outputs')


class Activity2Activity(Flow):

    destination = models.ForeignKey(Activity, on_delete=models.CASCADE,
                                    related_name='Inputs')
    origin = models.ForeignKey(Activity, on_delete=models.CASCADE,
                               related_name='Outputs')


class Actor2Actor(Flow):

    destination = models.ForeignKey(Actor, on_delete=models.CASCADE,
                                    related_name='Inputs')
    origin = models.ForeignKey(Actor, on_delete=models.CASCADE,
                               related_name='Outputs')


class Stock(models.Model):

    # stocks relate to only one node, also data will be entered by the users
    material = models.CharField(max_length=255, choices=Flow.material_choices, blank=True)
    amount = models.PositiveIntegerField(blank=True)
    quality = models.CharField(max_length=255, choices=Flow.quality_choices, blank=True)

    class Meta:
        abstract = True


class GroupStock(Stock):

        origin = models.ForeignKey(ActivityGroup, on_delete=models.CASCADE,
                                   related_name='Stocks')


class ActivityStock(Stock):

        origin = models.ForeignKey(Activity, on_delete=models.CASCADE,
                                   related_name='Stocks')


class ActorStock(Stock):

        origin = models.ForeignKey(Actor, on_delete=models.CASCADE,
                                   related_name='Stocks')

"""Models for the first spatial sankey diagram"""

from django.db import models


class Nodes(models.Model):

    location = models.CharField(max_length=255)
    x_coord = models.FloatField()
    y_coord = models.FloatField()


class Links(models.Model):

    id_from = models.CharField(max_length=255)
    id_to = models.CharField(max_length=255)

    weight = models.FloatField()


class Person(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

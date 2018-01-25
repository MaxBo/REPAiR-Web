"""Models for the first spatial sankey diagram"""

from django.db import models
from repair.apps.login.models.bases import GDSEModel


class Nodes(GDSEModel):

    location = models.CharField(max_length=255)
    x_coord = models.FloatField()
    y_coord = models.FloatField()


class Links(GDSEModel):

    id_from = models.CharField(max_length=255)
    id_to = models.CharField(max_length=255)

    weight = models.FloatField()


class Person(GDSEModel):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

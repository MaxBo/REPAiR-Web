from django.db import models

# Create your models here.

class Nodes(models.Model):
    #node_id = models.IntegerField(primary_key=True)
    location = models.CharField(max_length=255)
    x_coord = models.FloatField()
    y_coord = models.FloatField()


class Links(models.Model):
    #link_id = models.IntegerField(primary_key=True)
    id_from = models.CharField(max_length=255)
    id_to = models.CharField(max_length=255)
    #link_description = models.CharField(max_length=100)
    weight = models.FloatField()


class Person(models.Model):
    first_name = models.CharField(max_length = 255)
    last_name = models.CharField(max_length = 255)
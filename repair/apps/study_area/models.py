from django.db import models

# Create your models here.

class Nodes(models.Model):
    node_id = models.IntegerField(primary_key=True)
    location = models.CharField(max_length=255)
    x_coord = models.FloatField()
    y_coord = models.FloatField()

    def __str__(self):

        return ' '.join([self.location])


class Links(models.Model):
    link_id = models.IntegerField(primary_key=True)
    id_from = models.IntegerField()
    id_to = models.IntegerField()
    link_description = models.CharField(max_length=100)
    weight = models.FloatField()

    def __str__(self):

        return ' '.join([self.link_description])
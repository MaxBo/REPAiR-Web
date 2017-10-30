from django.db import models
from repair.apps.login.models import GDSEUniqueNameModel, CaseStudy


class StakeholderCategory(GDSEUniqueNameModel):
    casestudy = models.ForeignKey(CaseStudy)
    name = models.TextField()


class Stakeholder(GDSEUniqueNameModel):
    stakeholder_category = models.ForeignKey(StakeholderCategory)
    name = models.TextField()

    @property
    def casestudy(self):
        return self.stakeholder_category.casestudy


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
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

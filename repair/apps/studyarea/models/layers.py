from django.db import models

from repair.apps.login.models import GDSEUniqueNameModel, CaseStudy, GDSEModel


class LayerCategory(GDSEUniqueNameModel):
    """Layer Category"""
    name = models.TextField()
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)


class Layer(GDSEModel):
    """"""
    category = models.ForeignKey(LayerCategory, on_delete=models.CASCADE)
    name = models.TextField()
    url = models.TextField()
    description = models.TextField(null=True, blank=True)
    user = models.TextField(null=True, blank=True)
    password = models.TextField(null=True, blank=True)
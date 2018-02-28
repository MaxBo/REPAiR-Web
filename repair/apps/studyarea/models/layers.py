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
    description = models.TextField(null=True, blank=True)
    
    #service url
    url = models.TextField()
    
    # authentication for service
    credentials_needed = models.BooleanField(default=False)
    user = models.TextField(null=True, blank=True)
    password = models.TextField(null=True, blank=True)
    
    # service query parameters 
    service_version = models.TextField(null=True, blank=True)
    service_layers = models.TextField(null=True, blank=True)
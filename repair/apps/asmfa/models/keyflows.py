# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from repair.apps.login.models import (CaseStudy, GDSEModel)


class Keyflow(GDSEModel):
    # the former "Material" class - not to confuse with the other one
    keyflow_choices = (("Org", "Organic"),
                       ("CDW", "Construction & Demolition"),
                       ("Food", "Food"),
                       ("MSW", "Municipal Solid Waste"),
                       ("PCPW", "Post-Consumer Plastic"),
                       ("HHW", "Household Hazardous Waste"))
    code = models.TextField(choices=keyflow_choices)
    name = models.TextField()
    casestudies = models.ManyToManyField(CaseStudy,
                                         through='KeyflowInCasestudy')


class KeyflowInCasestudy(GDSEModel):
    keyflow = models.ForeignKey(Keyflow, on_delete=models.CASCADE,
                                related_name='products')
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    note = models.TextField(default='', blank=True)

    def __str__(self):
        return 'KeyflowInCasestudy {pk}: {k} in {c}'.format(
            pk=self.pk, k=self.keyflow, c=self.casestudy)


class Product(GDSEModel):

    # not sure about the max length, leaving everywhere 255 for now
    name = models.CharField(max_length=255, null=True)
    default = models.BooleanField(default=True)
    keyflow = models.ForeignKey(KeyflowInCasestudy, on_delete=models.CASCADE,
                                related_name='products')


class Material(GDSEModel):

    # not the same as the former Material class that has been renamed to Keyflow
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    flowType = models.CharField(max_length=255, null=True)


class ProductFraction(GDSEModel):

    fraction = models.FloatField(default=1)

    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name='fractions')
    material = models.ForeignKey(Material, on_delete=models.CASCADE,
                                 related_name='products')

    def __str__(self):
        return '{}: {}'.format(self.product, self.material)

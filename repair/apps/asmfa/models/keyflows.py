# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from collections import defaultdict

from repair.apps.login.models import (CaseStudy, GDSEModel)
from repair.apps.publications.models import PublicationInCasestudy
from repair.apps.utils.protect_cascade import PROTECT_CASCADE


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


class Material(GDSEModel):

    name = models.CharField(max_length=255)
    keyflow = models.ForeignKey(KeyflowInCasestudy, on_delete=PROTECT_CASCADE,
                                null=True)
    level = models.IntegerField()
    parent = models.ForeignKey('self', on_delete=PROTECT_CASCADE, null=True,
                               related_name='submaterials')

    @property
    def descendants(self):
        """ all children of the material (deep traversal) """
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.descendants)
        return descendants

    @property
    def children(self):
        """ direct children of the material traversal """
        return Material.objects.filter(parent=self.id)

    def is_descendant(self, *args):
        ''' return True if material is descendant of any of
        the passed materials '''
        parent = self.parent
        materials = list(args)
        while parent:
            if parent in materials: return True
            parent = parent.parent
        return False

    def ancestor(self, *args):
        '''
        return the first ancestor found
        if material is descendant of any of the passed materials
        else return None
        '''
        parent = self.parent
        materials = list(args)
        while parent:
            if parent in materials:
                return parent
            parent = parent.parent
        return None


class Composition(GDSEModel):

    name = models.CharField(max_length=255, blank=True)
    nace = models.CharField(max_length=255, blank=True)
    keyflow = models.ForeignKey(KeyflowInCasestudy, on_delete=PROTECT_CASCADE,
                                null=True)

    @property
    def is_custom(self):
        """
        returns true, if composition is neither product or waste

        Returns
        -------
        bool
        """
        is_waste = getattr(self, 'waste', None) is not None
        is_product = getattr(self, 'product', None) is not None
        is_custom = not (is_waste or is_product)
        return is_custom

    #def aggregate_by_materials(self, materials):
        #aggregation = defaultdict.fromkeys(materials, 0)
        #for fraction in self.fractions.iterator():
            #for material in materials:
                #if fraction.material.is_descendant(material):
                    #aggregation[material] += fraction.fraction
        #return


class Product(Composition):

    cpa = models.CharField(max_length=255)


class Waste(Composition):

    ewc = models.CharField(max_length=255)
    wastetype = models.CharField(max_length=255)
    hazardous = models.BooleanField()


class ProductFraction(GDSEModel):

    fraction = models.FloatField()
    material = models.ForeignKey(Material, on_delete=PROTECT_CASCADE,
                                 related_name='items')
    composition = models.ForeignKey(Composition, on_delete=models.CASCADE,
                                    related_name='fractions', null=True)
    publication = models.ForeignKey(PublicationInCasestudy, null=True,
                                    on_delete=models.SET_NULL,
                                    related_name='fractions')
    avoidable = models.BooleanField(default=True)

    def __str__(self):
        return '{}: {}'.format(self.composition, self.material)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.functional import cached_property

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
    level = models.IntegerField(default=1)
    parent = models.ForeignKey('self', on_delete=PROTECT_CASCADE, null=True,
                               related_name='submaterials')

    class Meta(GDSEModel.Meta):
        unique_together = ('name', 'keyflow', 'level')

    @cached_property
    def descendants(self):
        """ all children of the material (deep traversal) """
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.descendants)
        return descendants

    @cached_property
    def children(self):
        """ direct children of the material traversal """
        return Material.objects.filter(parent=self.id)

    @cached_property
    def top_ancestor(self):
        ancestor = self
        parent = self.parent
        i = 0
        while parent:
            ancestor = parent
            parent = parent.parent
            i += 1
            if i > 100:
                raise RecursionError(
                    'There appears to be a cycle in ancestry '
                    'of material {} - {}'
                    .format(self.id, self.name))
        return ancestor

    def is_descendant(self, *args):
        ''' return True if material is descendant of any of
        the passed materials '''
        parent = self.parent
        materials = list(args)
        i = 0
        while parent:
            if parent in materials: return True
            parent = parent.parent
            i += 1
            if i > 1000:
                raise RecursionError(
                    'There seems to be an cycle in ancestry of material {} - {}'
                    .format(self.id, self.name))
        return False

    def ancestor(self, *args):
        '''
        return the first ancestor found
        if material is descendant of any of the passed materials
        else return None
        '''
        parent = self.parent
        materials = list(args)
        i = 0
        while parent:
            if parent in materials:
                return parent
            parent = parent.parent
            i += 1
            if i > 1000:
                raise RecursionError(
                    'There seems to be an cycle in ancestry of material {} - {}'
                    .format(self.id, self.name))
        return None

    def save(self, *args, **kwargs):
        '''auto set level'''
        self.level = 1 if self.parent is None else self.parent.level + 1
        super().save(*args, **kwargs)


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


class Process(GDSEModel):
    name = models.TextField()


class Product(Composition):

    cpa = models.CharField(max_length=255, default='')


class Waste(Composition):

    ewc = models.CharField(max_length=255, default='')
    wastetype = models.CharField(max_length=255, default='')
    hazardous = models.BooleanField(default=False)


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
    hazardous = models.BooleanField(default=True)

    def __str__(self):
        return '{}: {}'.format(self.composition, self.material)

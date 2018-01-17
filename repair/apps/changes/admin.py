# -*- coding: utf-8 -*-
from django.contrib import admin
from . import models


@admin.register(models.SolutionCategory)
class SolutionCategoryAdmin(admin.ModelAdmin):
    """SolutionCategory Admin"""


class SolutionRatioOneUnitInline(admin.StackedInline):
    model = models.SolutionRatioOneUnit


@admin.register(models.Solution)
class SolutionAdmin(admin.ModelAdmin):
    """Solution Admin"""
    inlines = [
        SolutionRatioOneUnitInline,
    ]


class SolutionsInline(admin.StackedInline):
    model = models.Implementation.solutions.through


@admin.register(models.Implementation)
class ImplementationAdmin(admin.ModelAdmin):
    """Implementation Admin"""
    inlines = (SolutionsInline, )


@admin.register(models.Strategy)
class StrategyAdmin(admin.ModelAdmin):
    """Strategy Admin"""


class SolutionInImplementationQuantityInline(admin.StackedInline):
    model = models.SolutionInImplementationQuantity


class SolutionInImplementationGeometryInline(admin.StackedInline):
    model = models.SolutionInImplementationGeometry


class SolutionInImplementationNoteInline(admin.StackedInline):
    model = models.SolutionInImplementationNote


@admin.register(models.SolutionInImplementation)
class SolutionInImplementationAdmin(admin.ModelAdmin):
    """SolutionInImplementation Admin"""
    inlines = (SolutionInImplementationQuantityInline,
               SolutionInImplementationGeometryInline,
               SolutionInImplementationNoteInline,
               )




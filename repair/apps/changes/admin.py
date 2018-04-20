# -*- coding: utf-8 -*-
from django.contrib import admin
from reversion.admin import VersionAdmin
from . import models


@admin.register(models.Unit)
class SolutionCategoryAdmin(VersionAdmin):
    """Unit Admin"""


@admin.register(models.SolutionCategory)
class SolutionCategoryAdmin(VersionAdmin):
    """SolutionCategory Admin"""


@admin.register(models.SolutionRatioOneUnit)
class SolutionRatioOneUnitAdmin(VersionAdmin):
    """"""


class SolutionRatioOneUnitInline(admin.StackedInline):
    model = models.SolutionRatioOneUnit


@admin.register(models.Solution)
class SolutionAdmin(VersionAdmin):
    """Solution Admin"""
    inlines = [
        SolutionRatioOneUnitInline,
    ]


class SolutionsInline(admin.StackedInline):
    model = models.Implementation.solutions.through


@admin.register(models.Implementation)
class ImplementationAdmin(VersionAdmin):
    """Implementation Admin"""
    inlines = (SolutionsInline, )


@admin.register(models.Strategy)
class StrategyAdmin(VersionAdmin):
    """Strategy Admin"""


@admin.register(models.SolutionInImplementationQuantity)
class SolutionInImplementationQuantityAdmin(VersionAdmin):
    """"""


class SolutionInImplementationQuantityInline(admin.StackedInline):
    model = models.SolutionInImplementationQuantity


@admin.register(models.SolutionInImplementation)
class SolutionInImplementationAdmin(VersionAdmin):
    """SolutionInImplementation Admin"""
    inlines = (SolutionInImplementationQuantityInline,
               )




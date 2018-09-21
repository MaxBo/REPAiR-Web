# -*- coding: utf-8 -*-
from repair.apps import admin
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
    model = models.Strategy.solutions.through


@admin.register(models.Strategy)
class ImplementationAdmin(VersionAdmin):
    """Implementation Admin"""
    inlines = (SolutionsInline, )


@admin.register(models.SolutionInStrategyQuantity)
class SolutionInImplementationQuantityAdmin(VersionAdmin):
    """"""


class SolutionInImplementationQuantityInline(admin.StackedInline):
    model = models.SolutionInStrategyQuantity


@admin.register(models.SolutionInStrategy)
class SolutionInImplementationAdmin(VersionAdmin):
    """SolutionInImplementation Admin"""
    inlines = (SolutionInImplementationQuantityInline,
               )




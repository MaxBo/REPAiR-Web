# -*- coding: utf-8 -*-
from repair.apps import admin
from reversion.admin import VersionAdmin
from . import models


@admin.register(models.SolutionCategory)
class SolutionCategoryAdmin(VersionAdmin):
    """SolutionCategory Admin"""


@admin.register(models.Solution)
class SolutionAdmin(VersionAdmin):
    """Solution Admin"""

class SolutionsInline(admin.StackedInline):
    model = models.Strategy.solutions.through


@admin.register(models.Strategy)
class ImplementationAdmin(VersionAdmin):
    """Implementation Admin"""
    inlines = (SolutionsInline, )


@admin.register(models.ImplementationQuantity)
class ImplementationQuantityAdmin(VersionAdmin):
    """"""


class ImplementationQuantityInline(admin.StackedInline):
    model = models.ImplementationQuantity


@admin.register(models.SolutionInStrategy)
class SolutionInStrategyAdmin(VersionAdmin):
    """SolutionInImplementation Admin"""
    inlines = (ImplementationQuantityInline,
               )




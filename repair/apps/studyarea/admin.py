# -*- coding: utf-8 -*-
from repair.apps import admin
from . import models


@admin.register(models.Area)
class AreaAdmin(admin.ModelAdmin):
    """Area Admin"""


@admin.register(models.AdminLevels)
class AdminLevelsAdmin(admin.ModelAdmin):
    """AdminLevels Admin"""


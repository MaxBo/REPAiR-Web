# -*- coding: utf-8 -*-
from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin as VersionAdmin
from . import models


@admin.register(models.Aim)
class AimAdmin(VersionAdmin):
    """Area Admin"""

@admin.register(models.Challenge)
class ChallengeAdmin(VersionAdmin):
    """Versioning of Challenge"""


@admin.register(models.Target)
class TargetAdmin(VersionAdmin):
    """Versioning of Target"""


@admin.register(models.SustainabilityField)
class SustainabilityAdmin(VersionAdmin):
    """Versioning of SustainabilityField"""


@admin.register(models.AreaOfProtection)
class AreaOfProtectionAdmin(VersionAdmin):
    """Versioning of AreaOfProtection"""


@admin.register(models.ImpactCategory)
class ImpactCategoryAdmin(VersionAdmin):
    """Versioning of ImpactCategory"""


@admin.register(models.ImpactCategoryInSustainability)
class ImpactCategoryInSustainabilityAdmin(VersionAdmin):
    """Versioning of ImpactCategoryInSustainability"""


@admin.register(models.TargetSpatialReference)
class TargetSpatialReferenceAdmin(VersionAdmin):
    """Versioning of TargetSpatialReference"""


@admin.register(models.TargetValue)
class TargetValueAdmin(VersionAdmin):
    """Versioning of TargetValue"""


@admin.register(models.IndicatorCharacterisation)
class IndicatorCharacterisationAdmin(VersionAdmin):
    """Versioning of IndicatorCharacterisation"""
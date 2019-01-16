from repair.apps import admin
from reversion_compare.admin import CompareVersionAdmin as VersionAdmin
from django.contrib.gis.admin import GeoModelAdmin
from repair.apps.login.models import (CaseStudy, )
from repair.apps.studyarea.models import (StakeholderCategory,
                                          Stakeholder,
                                          )

from repair.apps.asmfa.models import (Actor,
                                      Activity,
                                      ActivityGroup,
                                      ActorStock,
                                      ActivityStock,
                                      GroupStock,
                                      Actor2Actor,
                                      Activity2Activity,
                                      Group2Group,
                                      Material,
                                      Product,
                                      ProductFraction,
                                      AdministrativeLocation,
                                      OperationalLocation,
                                      KeyflowInCasestudy,
                                      Composition
                                    )

from publications_bootstrap.models import Publication


@admin.register(CaseStudy)
class CaseStudyAdmin(GeoModelAdmin, VersionAdmin):
    """Versioning of casestudy"""


@admin.register(Composition)
class CompositionAdmin(VersionAdmin):
    """Versioning of composition"""


@admin.register(KeyflowInCasestudy)
class KeyflowInCasestudyAdmin(VersionAdmin):
    """Versioning of KeyflowInCasestudy"""


@admin.register(StakeholderCategory)
class StakeholderCategoryAdmin(VersionAdmin):
    """Versioning of StakeholderCategory"""


@admin.register(Stakeholder)
class StakeholderAdmin(VersionAdmin):
    """Versioning of Stakeholder"""


@admin.register(ActivityGroup)
class ActivityGroupAdmin(VersionAdmin):
    """Versioning of ActivityGroup"""

@admin.register(Activity)
class ActivityAdmin(VersionAdmin):
    """Versioning of Activity"""


@admin.register(Actor)
class ActorAdmin(VersionAdmin):
    """Versioning of Actor"""


@admin.register(GroupStock)
class GroupStockAdmin(VersionAdmin):
    """Versioning of GroupStock"""


@admin.register(ActivityStock)
class ActivityStockAdmin(VersionAdmin):
    """Versioning of ActivityStock"""


@admin.register(ActorStock)
class ActorStockAdmin(VersionAdmin):
    """Versioning of ActorStock"""


@admin.register(Group2Group)
class Group2GroupAdmin(VersionAdmin):
    """Versioning of Group2Group"""


@admin.register(Activity2Activity)
class Activity2ActivityAdmin(VersionAdmin):
    """Versioning of Activity2Activity"""


@admin.register(Actor2Actor)
class Actor2ActorAdmin(VersionAdmin):
    """Versioning of Actor2Actor"""


@admin.register(Material)
class MaterialAdmin(VersionAdmin):
    """Versioning of Material"""


@admin.register(Product)
class ProductAdmin(VersionAdmin):
    """Versioning of Product"""


@admin.register(ProductFraction)
class ProductFractionAdmin(VersionAdmin):
    """Versioning of ProductFraction"""


@admin.register(AdministrativeLocation)
class AdministrativeLocationAdmin(VersionAdmin):
    """Versioning of AdministrativeLocation"""


@admin.register(OperationalLocation)
class OperationalLocationAdmin(VersionAdmin):
    """Versioning of OperationalLocation"""

#from publications_bootstrap.admin.publicationadmin import PublicationAdmin
#@admin.site.unregister(Publication)
#@admin.register(Publication)
#class PublicationAdmin(VersionAdmin, PublicationAdmin):
    #"""Versioning of Publication"""

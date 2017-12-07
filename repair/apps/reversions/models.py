from django.contrib import admin
from reversion.admin import VersionAdmin
from repair.apps.login.models import (CaseStudy, )
from repair.apps.studyarea.models import (StakeholderCategory,
                                          Stakeholder,
                                          )

@admin.register(CaseStudy)
class CaseStudyAdmin(VersionAdmin):
    """Versioning of casestudy"""


@admin.register(StakeholderCategory)
class StakeholderCategoryAdmin(VersionAdmin):
    """Versioning of StakeholderCategory"""


@admin.register(Stakeholder)
class StakeholderAdmin(VersionAdmin):
    """Versioning of Stakeholder"""


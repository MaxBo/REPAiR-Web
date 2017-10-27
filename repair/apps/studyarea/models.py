from django.db import models
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.db.models import signals
from repair.apps.login.models import GDSEUniqueNameModel, CaseStudy


class StakeholderCategory(GDSEUniqueNameModel):
    casestudy = models.ForeignKey(CaseStudy)
    name = models.TextField()


class Stakeholder(GDSEUniqueNameModel):
    stakeholder_category = models.ForeignKey(StakeholderCategory)
    name = models.TextField()

    @property
    def casestudy(self):
        return self.stakeholder_category.casestudy

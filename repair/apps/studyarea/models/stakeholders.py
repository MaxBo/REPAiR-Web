
from django.db import models
from repair.apps.login.models import GDSEUniqueNameModel, CaseStudy
from repair.apps.utils.protect_cascade import PROTECT_CASCADE


class StakeholderCategory(GDSEUniqueNameModel):
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    name = models.TextField()


class Stakeholder(GDSEUniqueNameModel):
    stakeholder_category = models.ForeignKey(StakeholderCategory,
                                             on_delete=PROTECT_CASCADE)
    name = models.TextField()

    @property
    def casestudy(self):
        return self.stakeholder_category.casestudy

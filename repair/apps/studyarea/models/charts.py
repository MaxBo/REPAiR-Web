
from django.db import models
from repair.apps.login.models import GDSEModel, CaseStudy
from repair.apps.utils.protect_cascade import PROTECT_CASCADE


class ChartCategory(GDSEModel):
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)


class Chart(GDSEModel):
    chart_category = models.ForeignKey(ChartCategory,
                                       on_delete=PROTECT_CASCADE)
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='charts')

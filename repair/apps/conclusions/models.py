from django.db import models

from repair.apps.login.models.bases import GDSEModel
from repair.apps.utils.protect_cascade import PROTECT_CASCADE
from repair.apps.asmfa.models.keyflows import KeyflowInCasestudy
from repair.apps.login.models import CaseStudy


STEP_CHOICES = (
    (0, 'None'),
    (1, 'Objectives'),
    (2, 'Flow Targets'),
    (3, 'Strategies'),
    (4, 'Modified Flows'),
    (5, 'Sustainability')
)


class ConsensusLevel(GDSEModel):
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    name = models.TextField()
    priority = models.IntegerField(default=0)


class Section(GDSEModel):
    casestudy = models.ForeignKey(CaseStudy, on_delete=models.CASCADE)
    name = models.TextField()
    priority = models.IntegerField(default=0)


class Conclusion(GDSEModel):
    keyflow = models.ForeignKey(KeyflowInCasestudy, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    link = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='conclusions', blank=True, null=True)
    consensus_level = models.ForeignKey(ConsensusLevel,
                                        on_delete=PROTECT_CASCADE)
    section = models.ForeignKey(Section, on_delete=PROTECT_CASCADE)
    step = models.IntegerField(choices=STEP_CHOICES, default=0)

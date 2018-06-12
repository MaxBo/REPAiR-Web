
from django.contrib.gis.db import models
from repair.apps.login.models import (GDSEUniqueNameModel,
                                      UserInCasestudy)

from repair.apps.studyarea.models import Stakeholder
from .implementations import Implementation
from repair.apps.utils.protect_cascade import PROTECT_CASCADE


class Strategy(GDSEUniqueNameModel):
    user = models.ForeignKey(UserInCasestudy, on_delete=models.CASCADE)
    name = models.TextField()
    coordinator = models.ForeignKey(Stakeholder,
                                    on_delete=PROTECT_CASCADE)
    implementations = models.ManyToManyField(Implementation)

    @property
    def participants(self):
        """
        look for all stakeholders that participate
        in any of the implementations
        """
        # start with the coordinator
        participants = {self.coordinator}
        for implementation in self.implementations.all():
            for participant in implementation.participants:
                participants.add(participant)
        return participants

    @property
    def casestudy(self):
        return self.user.casestudy

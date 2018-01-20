
from django.contrib.gis.db import models
from repair.apps.login.models import (GDSEUniqueNameModel,
                                      UserInCasestudy)

from repair.apps.studyarea.models import Stakeholder
from .implementations import Implementation


class Strategy(GDSEUniqueNameModel):
    user = models.ForeignKey(UserInCasestudy)
    name = models.TextField()
    coordinator = models.ForeignKey(Stakeholder, default=1)
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

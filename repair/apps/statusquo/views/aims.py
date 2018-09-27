from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView
from plotly.offline import plot
from plotly.graph_objs import (Bar, Marker, Histogram2dContour, Contours,
                               Layout, Figure, Data)
from rest_framework import viewsets
from repair.views import ModeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
import numpy as np
from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet,
                                     ReadUpdatePermissionViewSet)
from repair.apps.statusquo.serializers import (AimSerializer,
                                               AimPostSerializer,
                                               UserObjectiveSerializer)
from repair.apps.statusquo.models import Aim, UserObjective


class AimViewSet(CasestudyViewSetMixin,
                 ModelPermissionViewSet):
    queryset = Aim.objects.all()
    serializer_class = AimSerializer
    serializers = {'create': AimPostSerializer,
                   'update': AimPostSerializer, }

    def get_queryset(self):
        aims = Aim.objects.all()
        casestudy_pk = self.kwargs.get('casestudy_pk')
        if casestudy_pk is not None:
            aims = aims.filter(casestudy__id=casestudy_pk)
        return aims


class UserObjectiveViewSet(CasestudyViewSetMixin,
                           ModelPermissionViewSet):
    queryset = UserObjective.objects.all()
    serializer_class = UserObjectiveSerializer

    def get_queryset(self):
        user = self.request.user
        keyflow = self.request.query_params.get('keyflow')
        casestudy_pk = self.kwargs.get('casestudy_pk')
        keyflow_pk = self.kwargs.get('keyflow_pk')
        aims = Aim.objects.filter(casestudy__id=casestudy_pk)
        objectives = UserObjective.objects.filter(
            aim__casestudy__id=casestudy_pk,
            user=user
        )
        if keyflow is not None:
            aims = aims.filter(keyflow__id=keyflow)
            objectives = objectives.filter(aim__keyflow__id=keyflow)
        aims_in_objectives = objectives.values_list('aim__id', flat=True)
        missing_aims = aims.exclude(id__in=aims_in_objectives)
        # create missing objectives
        for aim in missing_aims:
            objective = UserObjective(aim=aim, user=user)
            objective.save()
        # query changed objectives
        if len(missing_aims) > 0:
            objectives = UserObjective.objects.filter(
                aim__casestudy__id=casestudy_pk,
                user=user
            )
        return objectives

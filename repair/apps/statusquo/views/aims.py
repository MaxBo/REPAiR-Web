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
                                               UserObjectiveSerializer,
                                               AreaOfProtectionSerializer)
from repair.apps.statusquo.models import Aim, UserObjective, AreaOfProtection


class AreaOfProtectionViewSet(ModelPermissionViewSet):
    queryset = AreaOfProtection.objects.all()
    serializer_class = AreaOfProtectionSerializer
    pagination_class = None


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
        return aims.order_by('keyflow', 'priority')


class UserObjectiveViewSet(CasestudyViewSetMixin,
                           ModelPermissionViewSet):
    queryset = UserObjective.objects.all()
    serializer_class = UserObjectiveSerializer

    def get_queryset(self):
        user = self.request.user
        all_users = self.request.query_params.get('all') in ['true', 'True']
        casestudy_pk = self.kwargs.get('casestudy_pk')
        keyflow_pk = self.kwargs.get('keyflow_pk')
        aims = Aim.objects.filter(casestudy__id=casestudy_pk)
        objectives = UserObjective.objects.all()

        keyflow_null = self.request.query_params.get('keyflow__isnull')
        if keyflow_null:
            aims = aims.filter(keyflow__isnull=True)
            objectives = objectives.filter(aim__keyflow__isnull=True)
        else:
            keyflow = self.request.query_params.get('keyflow')
            if keyflow is not None:
                aims = aims.filter(keyflow__id=keyflow)
                objectives = objectives.filter(aim__keyflow__id=keyflow)


        # by default query objectives of current user and create them, if they
        #  don't exist yet
        # can be overriden with all=true
        if not all_users:
            objectives = objectives.filter(
                aim__casestudy__id=casestudy_pk,
                user=user
            )
            aims_in_objectives = objectives.values_list('aim__id', flat=True)
            missing_aims = aims.exclude(id__in=aims_in_objectives)
            # create missing objectives
            for aim in missing_aims:
                objective = UserObjective(aim=aim, user=user)
                objective.save()
            # requery changed objectives
            if len(missing_aims) > 0:
                objectives = UserObjective.objects.filter(
                    aim__casestudy__id=casestudy_pk,
                    user=user
                )
                if keyflow_null:
                    objectives = objectives.filter(aim__keyflow__isnull=True)
                elif keyflow is not None:
                    objectives = objectives.filter(aim__keyflow__id=keyflow)
        return objectives

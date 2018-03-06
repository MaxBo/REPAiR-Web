from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView
from plotly.offline import plot
from plotly.graph_objs import (Bar, Marker, Histogram2dContour, Contours,
                               Layout, Figure, Data)
from django.utils.translation import ugettext as _
from rest_framework import viewsets
from repair.views import ModeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
import numpy as np
from repair.apps.login.views import  CasestudyViewSetMixin
from repair.apps.utils.views import (ModelPermissionViewSet,
                                     ReadUpdatePermissionViewSet)
from repair.apps.statusquo.serializers import (AimSerializer,
                                               AimPostSerializer)
from repair.apps.statusquo.models import Aim


class AimViewSet(CasestudyViewSetMixin,
                 ModelPermissionViewSet):
    queryset = Aim.objects.all()
    serializer_class = AimSerializer
    serializers = {'create': AimPostSerializer,
                   'update': AimPostSerializer, }
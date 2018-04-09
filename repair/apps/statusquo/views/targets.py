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
from repair.apps.statusquo.serializers import (
     AreaOfProtectionSerializer,
     ImpactCategorySerializer,
     ImpactCategoryInSustainabilitySerializer,
     SustainabilityFieldSerializer,
     TargetSerializer,
     TargetSpatialReferenceSerializer,
     TargetValueSerializer)

from repair.apps.statusquo.models import (
    AreaOfProtection,
    ImpactCategory,
    ImpactCategoryInSustainability,
    SustainabilityField,
    Target,
    TargetSpatialReference,
    TargetValue)

from repair.apps.statusquo.models import Aim
from repair.apps.statusquo.serializers import (AimSerializer,
                                               AimPostSerializer)


class TargetViewSet(CasestudyViewSetMixin,
                    ModelPermissionViewSet):
    queryset = Target.objects.all()
    serializer_class = TargetSerializer

    def list(self, request, *args, **kwargs):
        
        if (request.user.id and 'user' not in request.query_params and
            'user__in' not in request.query_params):
            self.queryset = self.queryset.filter(user__user__user_id=request.user.id)
        
        return super().list(request, *args, **kwargs)


class SustainabilityFieldViewSet(ModelPermissionViewSet):
    queryset = SustainabilityField.objects.all()
    serializer_class = SustainabilityFieldSerializer


class ImpactcategoryViewSet(ModelPermissionViewSet):
    queryset = ImpactCategory.objects.all()
    serializer_class = ImpactCategorySerializer


class ImpactCategoryInSustainabilityViewSet(ModelPermissionViewSet):
    queryset = ImpactCategory.objects.all()
    serializer_class = ImpactCategorySerializer

    def list(self, request, *args, **kwargs):
        super().check_permission(request, 'view')
        sus_field_pk = list(kwargs.values())[0]
        sus_field = SustainabilityField.objects.get(pk=sus_field_pk)
        areas_of_protection = [aep.id for aep in
                               sus_field.areaofprotection_set.all()]
        queryset = self.filter_queryset(
            self.get_queryset()).filter(area_of_protection__in=
                                        areas_of_protection)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AreaOfProtectionViewSet(ModelPermissionViewSet):
    queryset = AreaOfProtection.objects.all()
    serializer_class = AreaOfProtectionSerializer


class TargetValueViewSet(ModelPermissionViewSet):
    queryset = TargetValue.objects.all()
    serializer_class = TargetValueSerializer


class TargetSpatialReferenceViewSet(ModelPermissionViewSet):
    queryset = TargetSpatialReference.objects.all()
    serializer_class = TargetSpatialReferenceSerializer

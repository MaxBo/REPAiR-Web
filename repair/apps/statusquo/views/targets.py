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
from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet,
                                     ReadUpdatePermissionViewSet)
from rest_framework.response import Response
from repair.apps.statusquo.serializers import (
     ImpactCategorySerializer,
     ImpactCategoryInSustainabilitySerializer,
     SustainabilityFieldSerializer,
     TargetSpatialReferenceSerializer,
     TargetValueSerializer,
     FlowTargetSerializer,
     AimSerializer,
     AimPostSerializer
)

from repair.apps.statusquo.models import (
    ImpactCategory,
    ImpactCategoryInSustainability,
    SustainabilityField,
    TargetSpatialReference,
    TargetValue,
    FlowTarget,
    Aim
)


class SustainabilityFieldViewSet(ModelPermissionViewSet):
    queryset = SustainabilityField.objects.all()
    serializer_class = SustainabilityFieldSerializer
    pagination_class = None


class ImpactcategoryViewSet(ModelPermissionViewSet):
    queryset = ImpactCategory.objects.all()
    serializer_class = ImpactCategorySerializer
    pagination_class = None


class ImpactCategoryInSustainabilityViewSet(ModelPermissionViewSet):
    queryset = ImpactCategory.objects.all()
    serializer_class = ImpactCategorySerializer
    pagination_class = None

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


class TargetValueViewSet(ModelPermissionViewSet):
    queryset = TargetValue.objects.all()
    serializer_class = TargetValueSerializer
    pagination_class = None


class TargetSpatialReferenceViewSet(ModelPermissionViewSet):
    queryset = TargetSpatialReference.objects.all()
    serializer_class = TargetSpatialReferenceSerializer
    pagination_class = None


class FlowTargetViewSet(CasestudyViewSetMixin,
                        ModelPermissionViewSet):
    queryset = FlowTarget.objects.all()
    serializer_class = FlowTargetSerializer

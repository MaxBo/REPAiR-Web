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
                                               AimPostSerializer,
                                               ChallengeSerializer,
                                               ChallengePostSerializer,
                                               AreaOfProtectionSerializer,
                                               ImpactCategorySerializer,
                                               ImpactCategoryInSustainabilitySerializer,
                                               SustainabilityFieldSerializer,
                                               TargetSerializer,
                                               TargetSpatialReferenceSerializer,
                                               TargetValueSerializer)
from repair.apps.statusquo.models import (Aim,
                                          Challenge,
                                          AreaOfProtection,
                                          ImpactCategory,
                                          ImpactCategoryInSustainability,
                                          SustainabilityField,
                                          Target,
                                          TargetSpatialReference,
                                          TargetValue)


class Testgraph1(TemplateView):
    template_name = 'graph.html'

    def get_context_data(self, **kwargs):
        context = super(Testgraph1, self).get_context_data(**kwargs)
        values = Bar(x=['Malodorous air', 'Time-use waste sorting', 'GHG gases', 'Human toxicity', 'Air pollution', 'Ecotoxicity', 'Water use', 'Land use', 'Social costs'], y=[3.2, 8.8, 5.4, 6.9, 1.9, 9.7])
        data=Data([values])
        layout=Layout(title=_("Status Quo Sustainability AMA Focus Region"), xaxis={'title':'Indicators of sustainability'}, yaxis={'title':'sustainability value'}, height=350)
        figure=Figure(data=data,layout=layout)
        div = plot(figure, auto_open=False, output_type='div', show_link=False)

        return div


class StatusQuoView(LoginRequiredMixin, ModeView):

    def render_setup(self, request):
        return render(request, 'statusquo/setup/index.html', self.get_context_data())

    def render_workshop(self, request):
        template = loader.get_template('statusquo/workshop/index.html')
        context = self.get_context_data()
        context['indicatorgraph'] = Testgraph1().get_context_data()
        context['casestudies'] = self.casestudies()
        html = template.render(context, request)
        return HttpResponse(html)


class AimViewSet(CasestudyViewSetMixin,
                 ModelPermissionViewSet):
    queryset = Aim.objects.all()
    serializer_class = AimSerializer
    serializers = {'create': AimPostSerializer,
                   'update': AimPostSerializer, }


class ChallengeViewSet(CasestudyViewSetMixin,
                       ModelPermissionViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    serializers = {'create': ChallengePostSerializer,
                   'update': ChallengePostSerializer, }


class TargetViewSet(CasestudyViewSetMixin,
                    ModelPermissionViewSet):
    queryset = Target.objects.all()
    serializer_class = TargetSerializer


class SustainabilityFieldViewSet(ModelPermissionViewSet):
    queryset = SustainabilityField.objects.all()
    serializer_class = SustainabilityFieldSerializer


class ImpactcategoryViewSet(ModelPermissionViewSet):
    queryset = ImpactCategory.objects.all()
    serializer_class = ImpactCategorySerializer


class ImpactCategoryInSusytainabilityViewSet(ModelPermissionViewSet):
    queryset = ImpactCategory.objects.all()
    serializer_class = ImpactCategorySerializer

    def list(self, request, *args, **kwargs):
        super().check_permission(request, 'view')
        sus_field_pk = list(kwargs.values())[0]
        sus_field = SustainabilityField.objects.get(pk=sus_field_pk)
        areas_of_protection = [aep.id for aep in sus_field.areaofprotection_set.all()]
        queryset = self.filter_queryset(self.get_queryset()).filter(area_of_protection__in=areas_of_protection)

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
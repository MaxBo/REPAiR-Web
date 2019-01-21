from django.http import HttpResponse
from django.template import loader
from repair.apps.asmfa.models import KeyflowInCasestudy
from django.views.generic import TemplateView
from repair.views import ModeView
from django.shortcuts import render

from repair.apps.conclusions.models import Conclusion, ConsensusLevel, Section
from repair.apps.conclusions.serializers import (ConclusionSerializer,
                                                 ConsensusSerializer,
                                                 SectionSerializer)

from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet)


class ConclusionsIndexView(ModeView):

    def render_setup(self, request):
        context = self.get_context_data()
        return render(request, 'conclusions/setup.html', context)

    def render_workshop(self, request):
        casestudy = request.session.get('casestudy')
        keyflows = KeyflowInCasestudy.objects.filter(casestudy=casestudy)
        context = self.get_context_data()
        context['keyflows'] = keyflows

        return render(request, 'conclusions/workshop.html', context)


class ConclusionViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    queryset = Conclusion.objects.all()
    serializer_class = ConclusionSerializer


class ConsensusViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    queryset = ConsensusLevel.objects.all()
    serializer_class = ConsensusSerializer


class SectionViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    queryset = Section.objects.all()
    serializer_class = SectionSerializer




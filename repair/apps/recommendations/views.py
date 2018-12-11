from django.http import HttpResponse
from django.template import loader
from repair.apps.asmfa.models import KeyflowInCasestudy
from django.views.generic import TemplateView
from repair.views import ModeView
from django.shortcuts import render

class RecommendationsIndexView(ModeView):

    def render_setup(self, request):
        context = self.get_context_data()
        return render(request, 'recommendations/setup.html', context)

    def render_workshop(self, request):
        casestudy = request.session.get('casestudy')
        keyflows = KeyflowInCasestudy.objects.filter(casestudy=casestudy)
        context = self.get_context_data()
        context['keyflows'] = keyflows

        return render(request, 'recommendations/workshop.html', context)


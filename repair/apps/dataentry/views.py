from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView
from plotly.offline import iplot
import urllib
import json
from django.shortcuts import render
from plotly import offline
from plotly.graph_objs import Figure, Data, Layout
from repair.apps.login.models import CaseStudy
from repair.apps.asmfa.models import Material, KeyflowInCasestudy
from repair.views import BaseView
from django.contrib.auth.mixins import LoginRequiredMixin


class DataEntryView(LoginRequiredMixin, BaseView): 
    template_name = "dataentry/index.html"
    
    def get(self, request):
        # get the current casestudy
        url_pks = request.session.get('url_pks', {})
        
        casestudy = request.session.get('casestudy')
        keyflows = KeyflowInCasestudy.objects.filter(casestudy=casestudy)
        
        context = self.get_context_data()

        context['keyflows'] = keyflows

        return render(request, self.template_name, context)
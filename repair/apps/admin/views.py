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


class AdminView(BaseView): 
    template_name = "admin/index.html"
    title = 'Admin Area'
    
    def get(self, request):

        # get the current casestudy
        url_pks = request.session.get('url_pks', {})
        
        casestudy = request.session.get('casestudy')
        keyflows = KeyflowInCasestudy.objects.filter(casestudy=casestudy)

        context = {'casestudies': self.casestudies(),
                   'keyflows': keyflows,
                   }

        return render(request, self.template_name, context)
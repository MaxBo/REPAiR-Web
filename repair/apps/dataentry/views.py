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
from repair.apps.asmfa.models import KeyflowInCasestudy, Keyflow
from repair.views import BaseView
from django.contrib.auth.mixins import LoginRequiredMixin


class DataEntryView(LoginRequiredMixin, BaseView):
    template_name = "dataentry/index.html"

    def get(self, request):
        # get the current casestudy
        url_pks = request.session.get('url_pks', {})

        casestudy = request.session.get('casestudy')

        if not casestudy:
            return render(request, 'casestudy-missing.html',
                          self.get_context_data())

        kic = KeyflowInCasestudy.objects.filter(casestudy=casestudy)
        keyflows = Keyflow.objects.all()

        context = self.get_context_data()

        context['keyflows_in_casestudy'] = kic
        used = kic.values_list('keyflow', flat=True)
        unused = [k for k in keyflows if k.id not in used]
        context['unused_keyflows'] = unused

        return render(request, self.template_name, context)

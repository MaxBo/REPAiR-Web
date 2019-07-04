from django.http import HttpResponse
from django.template import loader
from rest_framework import viewsets
from repair.views import ModeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
import numpy as np

from repair.apps.asmfa.models import KeyflowInCasestudy
from repair.apps.statusquo.models import IndicatorType
from repair.apps.statusquo.views import computation


class IndicatorTemplate():
    def __init__(self, value, description, name, default_unit):
        (self.value, self.description,
         self.name, self.default_unit) = value, description, name, default_unit


class StatusQuoView(LoginRequiredMixin, ModeView):
    def render_setup(self, request):
        casestudy = request.session.get('casestudy')
        keyflows = KeyflowInCasestudy.objects.filter(casestudy=casestudy)

        context = self.get_context_data()

        indicators = []
        for ind in IndicatorType:
            ind_class = getattr(computation, ind.name)
            indtmpl = IndicatorTemplate(
                ind.name, ind_class.description, ind_class.name,
                ind_class.default_unit)
            indicators.append(indtmpl)

        context['keyflows'] = keyflows
        context['indicators'] = indicators
        return render(request, 'statusquo/index.html',
                      context)

    def render_workshop(self, request):
        # same entry point as in setup mode
        return self.render_setup(request)

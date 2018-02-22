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
        return render(request, 'statusquo/setup/index.html')
    
    def render_workshop(self, request):
        template = loader.get_template('statusquo/workshop/index.html')
        context = {}
        context['indicatorgraph'] = Testgraph1().get_context_data()
        context['casestudies'] = self.casestudies()
        html = template.render(context, request)
        return HttpResponse(html)

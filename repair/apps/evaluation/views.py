from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView
from plotly.offline import plot
from plotly.graph_objs import (Bar, Marker, Histogram2dContour, Contours,
                               Layout, Figure, Data)
from django.utils.translation import ugettext as _
from rest_framework import viewsets

import numpy as np  
class Testgraph1(TemplateView):
    template_name = 'graph.html'

    def get_context_data(self, **kwargs):
        context = super(Testgraph1, self).get_context_data(**kwargs)

        animals = Bar(x=['Index A', 'Index B', 'Index C', 'Index D', 'Index E', 'Index F'], y=[1000, 1400, 2300, 1800, 1300, 2000])
        data=Data([animals])
        layout=Layout(title=_("Plotly graph"), xaxis={'title':'x1'}, yaxis={'title':'x2'}, height=350)
        figure=Figure(data=data,layout=layout)
        div = plot(figure, auto_open=False, output_type='div', show_link=False)

        return div
    
def index(request):
    template = loader.get_template('status_quo/sq_evaluation.html')
    context = {}
    context['indicatorgraph'] = Testgraph1().get_context_data()
    html = template.render(context, request)
    return HttpResponse(html)
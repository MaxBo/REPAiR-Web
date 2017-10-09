from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView
from plotly.offline import plot
from plotly.graph_objs import (Scatter, Marker, Histogram2dContour, Contours,
                               Layout, Figure, Data)
from django.utils.translation import ugettext as _
from rest_framework import viewsets
from repair.apps.study_area.serializers import LinksSerializer, NodesSerializer
from repair.apps.study_area.models import Links, Nodes


import numpy as np

class Testgraph1(TemplateView):
    template_name = 'graph.html'

    def get_context_data(self, **kwargs):
        context = super(Testgraph1, self).get_context_data(**kwargs)

        x = [-2,0,4,6,7]
        y = [q**2-q+3 for q in x]
        trace1 = Scatter(x=x, y=y, marker={'color': 'red', 'symbol': 104, 'size': "10"},
                         mode="lines",  name='1st Trace')

        data=Data([trace1])
        layout=Layout(title=_("Plotly graph"), xaxis={'title':'x1'}, yaxis={'title':'x2'}, height=350)
        figure=Figure(data=data,layout=layout)
        div = plot(figure, auto_open=False, output_type='div', show_link=False)

        return div

class Testgraph2(TemplateView):

    def get_context_data(self, **kwargs):
        x = np.random.randn(2000)
        y = np.random.randn(2000)
        layout=Layout(title=_("Plotly Histogram"), height=350)
        figure=Figure(data=[Histogram2dContour(x=x, y=y, contours=Contours(coloring='heatmap')),
                       Scatter(x=x, y=y, mode='markers', marker=Marker(color='white', size=3, opacity=0.3))],
                      layout=layout)
        div = plot(figure, show_link=False, output_type='div')
        return div

class LinksViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Links.objects.all()
    serializer_class = LinksSerializer

class NodesViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Nodes.objects.all()
    serializer_class = NodesSerializer


def index(request):
    template = loader.get_template('study_area/index.html')
    
    context = {}
    context['graph1'] = Testgraph1().get_context_data()
    context['graph2'] = Testgraph2().get_context_data()
    
    html = template.render(context, request)
    return HttpResponse(html)
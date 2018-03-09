from django.views.generic import TemplateView
from django.utils.translation import ugettext as _

from plotly.offline import plot
from plotly.graph_objs import (Scatter, Marker, Histogram2dContour, Contours,
                               Layout, Figure, Data, Box)
import numpy as np
from repair.apps.asmfa.models import Actor
from django_pandas.io import read_frame


class Testgraph1(TemplateView):
    template_name = 'graph.html'

    def get_context_data(self, **kwargs):
        context = super(Testgraph1, self).get_context_data(**kwargs)
 
        actors = read_frame(Actor.objects.all())
        x = actors.activity
        y = actors.employees
        trace1 = Box(x=x, y=y,
                     marker={'color': 'red', 'symbol': 104, 'size': "10"},
                     #mode="lines",
                     name='1st Trace')

        data = Data([trace1])
        layout = Layout(title=_("Plotly graph"), xaxis={'title': 'x1'},
                        yaxis={'title': 'x2'}, height=350)
        figure = Figure(data=data, layout=layout)
        div = plot(figure, auto_open=False, output_type='div', show_link=False)

        return div


class Testgraph2(TemplateView):

    def get_context_data(self, **kwargs):
        x = np.random.randn(2000)
        y = np.random.randn(2000)
        layout = Layout(title=_("Plotly Histogram"), height=350)
        figure = Figure(data=[
            Histogram2dContour(x=x, y=y,
                               contours=Contours(coloring='heatmap')),
            Scatter(x=x, y=y,
                    mode='markers', marker=Marker(
                        color='white', size=3, opacity=0.3))],
                    layout=layout)
        div = plot(figure, show_link=False, output_type='div')
        return div

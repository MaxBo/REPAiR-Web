from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView
import plotly.offline as opy
import plotly.graph_objs as go

class Testgraph(TemplateView):
    template_name = 'graph.html'

    def get_context_data(self, **kwargs):
        context = super(Testgraph, self).get_context_data(**kwargs)

        x = [-2,0,4,6,7]
        y = [q**2-q+3 for q in x]
        trace1 = go.Scatter(x=x, y=y, marker={'color': 'red', 'symbol': 104, 'size': "10"},
                            mode="lines",  name='1st Trace')

        data=go.Data([trace1])
        layout=go.Layout(title="some diagram", xaxis={'title':'x1'}, yaxis={'title':'x2'})
        figure=go.Figure(data=data,layout=layout)
        div = opy.plot(figure, auto_open=False, output_type='div')

        return div

def index(request):
    template = loader.get_template('study_area/index.html')
    context = {}
    g = Testgraph()
    context['graph'] = g.get_context_data()
    html = template.render(context, request)
    return HttpResponse(html)    
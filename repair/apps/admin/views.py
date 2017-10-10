from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView
from plotly.offline import iplot
import urllib
import json
from plotly import offline
from plotly.graph_objs import Figure, Data, Layout, Sankey
from repair.apps.changes.models import CaseStudy

class SankeyTest(TemplateView):
    template_name = 'graph.html'

    def get_context_data(self, **kwargs):
        url = 'https://raw.githubusercontent.com/plotly/plotly.js/master/test/image/mocks/sankey_energy.json'
        response = urllib.request.urlopen(url)
        data = json.loads(response.read())
        
        data_trace = Sankey(
            domain = dict(
              x =  [0,1],
              y =  [0,1]
            ),
            orientation = "h",
            valueformat = ".0f",
            valuesuffix = "TWh",
            node = dict(
              pad = 15,
              thickness = 15,
              line = dict(
                color = "black",
                width = 0.5
              ),
              label =  data['data'][0]['node']['label'],
              color =  data['data'][0]['node']['color']
            ),
            link = dict(
              source =  data['data'][0]['link']['source'],
              target =  data['data'][0]['link']['target'],
              value =  data['data'][0]['link']['value'],
              label =  data['data'][0]['link']['label']
          ))
        
        layout =  Layout(
            title = "Example plotly sankey-diagram WITHOUT SUPPORT OF CYCLES",
            font = dict(
              size = 10
            ),
            height=800
        )
        data=Data([data_trace])
        
        figure = Figure(data=data, layout=layout)
        div = offline.plot(figure, show_link=False, output_type='div')

        return div

def index(request):
    template = loader.get_template('admin/index.html')
    
    context = {}
    context['sankey'] = SankeyTest().get_context_data()
    context['case_studies'] = CaseStudy.objects.order_by('id')
    context['flows'] = []
    
    html = template.render(context, request)
    return HttpResponse(html)
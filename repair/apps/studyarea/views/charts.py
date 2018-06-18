
from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet)

from repair.apps.studyarea.models import ChartCategory, Chart

from repair.apps.studyarea.serializers import (ChartCategorySerializer,
                                               ChartSerializer)
from plotly.offline import plot
from plotly.graph_objs import (Scatter, Marker, Histogram2dContour, Contours,
                               Layout, Figure, Data)
from django.http import HttpResponse
import numpy as np


class ChartCategoryViewSet(CasestudyViewSetMixin,
                                 ModelPermissionViewSet):
    queryset = ChartCategory.objects.all()
    serializer_class = ChartCategorySerializer


class ChartViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    queryset = Chart.objects.all()
    serializer_class = ChartSerializer
    
    def retrieve(self, request, **kwargs):
        x = np.random.rand(5)
        y = [q**2-q+3 for q in x]
        trace1 = Scatter(x=x, y=y, marker={'color': 'red', 'symbol': 104, 'size': "10"},
                         mode="lines",  name='1st Trace')

        data=Data([trace1])
        layout=Layout(title="some diagram", xaxis={'title':'x1'}, yaxis={'title':'x2'})
        figure=Figure(data=data,layout=layout)
        div = plot(figure, auto_open=False, include_plotlyjs=False, output_type='div', show_link=False)
        return HttpResponse(div)
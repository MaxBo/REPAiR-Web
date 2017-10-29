from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views.generic import TemplateView
from django.shortcuts import render
from rest_framework.filters import BaseFilterBackend
from django.utils.translation import ugettext as _
from rest_framework import viewsets
from rest_framework.response import Response

from plotly.offline import plot
from plotly.graph_objs import (Scatter, Marker, Histogram2dContour, Contours,
                               Layout, Figure, Data)
import numpy as np

from repair.apps.login.models import (CaseStudy, Profile, UserInCasestudy)
from repair.apps.studyarea.models import (StakeholderCategory,
                                          Stakeholder,
                                          )

from repair.apps.studyarea.serializers import (StakeholderCategorySerializer,
                                               StakeholderSerializer,
                                               )

#class IsCasestudyFilterBackend(BaseFilterBackend):
    #"""
    #Filter that shows only objects related to to the casestudy
    #"""
    #def filter_queryset(self, request, queryset, view):
        #casestudy = request.session.get('casestudy')
        #if casestudy:
            #queryset = queryset.filter(casestudy=casestudy)
        #else:
            #queryset = queryset.all()
        #return queryset.filter(casestudy=casestudy)


class StakeholderCategoryViewSet(viewsets.ModelViewSet):
    queryset = StakeholderCategory.objects.all()
    serializer_class = StakeholderCategorySerializer

    #filter_backends = (IsCasestudyFilterBackend, )


class StakeholderViewSet(viewsets.ModelViewSet):
    queryset = Stakeholder.objects.all()
    serializer_class = StakeholderSerializer


def index(request):
    casestudy_list = CaseStudy.objects.order_by('id')[:20]
    users = Profile.objects.order_by('id')[:20]

    # get the current casestudy
    casestudy = request.session.get('casestudy')
    if casestudy:
        stakeholder_category_list = \
            StakeholderCategory.objects.filter(casestudy=casestudy)
    else:
        stakeholder_category_list = StakeholderCategory.objects.all()

    context = {'casestudy_list': casestudy_list,
               'users': users,
               'stakeholder_category_list': stakeholder_category_list,
               }

    context['graph1'] = Testgraph1().get_context_data()
    context['graph2'] = Testgraph2().get_context_data()
    return render(request, 'studyarea/index.html', context)


def stakeholdercategories(request, stakeholdercategory_id):
    stakeholder_category = StakeholderCategory.objects.get(
        pk=stakeholder_category_id)
    stakeholders = stakeholder_category.stakeholder_set.all()
    context = {'stakeholder_category': stakeholder_category,
               'stakeholders': stakeholders,
               }
    return render(request, 'changes/stakeholder_category.html', context)


def stakeholders(request, stakeholder_id):
    stakeholder = Stakeholder.objects.get(pk=stakeholder_id)
    if request.method == 'POST':
        form = NameForm(request.POST)
        if form.is_valid():
            stakeholder.name = form.cleaned_data['name']
            stakeholder.full_clean()
            stakeholder.save()
            return HttpResponseRedirect(
                '/changes/stakeholdercategories/{}'.
                format(stakeholder.stakeholder_category.id))
    context = {'stakeholder': stakeholder,
               }
    return render(request, 'changes/stakeholder.html', context)


class Testgraph1(TemplateView):
    template_name = 'graph.html'

    def get_context_data(self, **kwargs):
        context = super(Testgraph1, self).get_context_data(**kwargs)

        x = [-2, 0, 4, 6, 7]
        y = [q**2 - q+3 for q in x]
        trace1 = Scatter(x=x, y=y,
                         marker={'color': 'red', 'symbol': 104, 'size': "10"},
                         mode="lines",  name='1st Trace')

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

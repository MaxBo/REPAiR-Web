from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views.generic import TemplateView
from django.shortcuts import render
from django.utils.translation import ugettext as _

from rest_framework.filters import BaseFilterBackend
from rest_framework import viewsets
from rest_framework.response import Response

from plotly.offline import plot
from plotly.graph_objs import (Scatter, Marker, Histogram2dContour, Contours,
                               Layout, Figure, Data)
import numpy as np

from repair.apps.login.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet)
from repair.apps.login.models import (CaseStudy, Profile, UserInCasestudy)
from repair.apps.studyarea.models import (StakeholderCategory,
                                          Stakeholder,
                                          AdminLevels,
                                          Area,
                                          )

from repair.apps.studyarea.serializers import (StakeholderCategorySerializer,
                                               StakeholderSerializer,
                                               AreaSubModels,
                                               AdminLevelSerializer,
                                               AreaSerializer,
                                               AreaGeoJsonSerializer,
                                               AreaGeoJsonPostSerializer,
                                               )

from repair.views import BaseView


class StakeholderCategoryViewSet(CasestudyViewSetMixin,
                                 ModelPermissionViewSet):
    add_perm = 'studyarea.add_stakeholdercategory'
    change_perm = 'studyarea.change_stakeholdercategory'
    delete_perm = 'studyarea.delete_stakeholdercategory'
    queryset = StakeholderCategory.objects.all()
    serializer_class = StakeholderCategorySerializer

    #filter_backends = (IsCasestudyFilterBackend, )


class StakeholderViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    add_perm = 'studyarea.add_stakeholder'
    change_perm = 'studyarea.change_stakeholder'
    delete_perm = 'studyarea.delete_stakeholder'
    queryset = Stakeholder.objects.all()
    serializer_class = StakeholderSerializer


class AdminLevelViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    add_perm = 'studyarea.add_adminlevels'
    change_perm = 'studyarea.change_adminlevels'
    delete_perm = 'studyarea.delete_adminlevels'
    queryset = AdminLevels.objects.all()
    serializer_class = AdminLevelSerializer


class AreaViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    add_perm = 'studyarea.add_area'
    change_perm = 'studyarea.change_area'
    delete_perm = 'studyarea.delete_area'
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    serializers = {'retrieve': AreaGeoJsonSerializer,
                   'update': AreaGeoJsonSerializer,
                   'partial_update': AreaGeoJsonSerializer,
                   'create': AreaGeoJsonPostSerializer,}

    def _filter(self, lookup_args, query_params={}, SerializerClass=None):
        params = {k: v for k, v in query_params.items()}
        parent_level = int(params.pop('parent_level', 0))
        parent_id = params.pop('parent_id', None)

        if not parent_level and parent_id is None:
            return super()._filter(lookup_args,
                                   query_params=query_params,
                                   SerializerClass=SerializerClass)

        casestudy = lookup_args['casestudy_pk']
        level_pk = int(lookup_args['level_pk'])
        own_level = AdminLevels.objects.get(pk=level_pk)
        if not parent_level:
            parent_level = Area.objects.get(pk=parent_id).level.level
        levels = AdminLevels.objects.filter(casestudy__id=casestudy,
                                               level__gt=parent_level,
                                               level__lte=own_level.level)
        level_ids = [l.level for l in levels]

        parents = [AreaSubModels[parent_level].objects.get(pk=parent_id)]
        for level_id in level_ids:
            model = AreaSubModels[level_id]
            areas = model.objects.filter(parent_area__in=parents)
            parents.extend(areas)
        filter_args = self.get_filter_args(queryset=areas,
                                           query_params=params)
        queryset = areas.filter(**filter_args)
        return queryset


class StudyAreaIndexView(BaseView):

    def get(self, request):
        casestudy_list = CaseStudy.objects.order_by('id')[:20]
        users = Profile.objects.order_by('id')[:20]

        # get the current casestudy
        url_pks = request.session.get('url_pks', {})
        casestudy = url_pks.get('casestudy_pk')
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
        context['casestudies'] = self.casestudies()
        return render(request, 'studyarea/index.html', context)


class StakeholderCategoriesView(BaseView):

    def get(self, request, stakeholdercategory_id):
        stakeholder_category = StakeholderCategory.objects.get(
            pk=stakeholder_category_id)
        stakeholders = stakeholder_category.stakeholder_set.all()
        context = {'stakeholder_category': stakeholder_category,
                   'stakeholders': stakeholders,
                   }
        context['casestudies'] = self.casestudies()
        return render(request, 'changes/stakeholder_category.html', context)


class StakeholderView(BaseView):
    def get(self, request, stakeholder_id):
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
        context['casestudies'] = self.casestudies()
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

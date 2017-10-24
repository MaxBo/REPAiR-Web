from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views.generic import TemplateView
from django.shortcuts import render
import django.db.models

from django.utils.translation import ugettext as _
from rest_framework import viewsets
from repair.apps.changes.models import (CaseStudy,
                                        Unit,
                                        User,
                                        UserInCasestudy,
                                        StakeholderCategory,
                                        Stakeholder,
                                        SolutionCategory,
                                        Solution,
                                        Implementation,
                                        SolutionInImplementation,
                                        Strategy,
                                        )

from repair.apps.changes.serializers import (CaseStudySerializer,
                                             StakeholderCategorySerializer,
                                             StakeholderSerializer,
                                             SolutionSerializer,
                                             SolutionCategorySerializer,
                                             )

class CaseStudyViewSet(viewsets.ModelViewSet):
    queryset = CaseStudy.objects.all()
    serializer_class = CaseStudySerializer


class StakeholderCategoryViewSet(viewsets.ModelViewSet):
    queryset = StakeholderCategory.objects.all()
    serializer_class = StakeholderCategorySerializer


class StakeholderViewSet(viewsets.ModelViewSet):
    queryset = Stakeholder.objects.all()
    serializer_class = StakeholderSerializer


class SolutionCategoryViewSet(viewsets.ModelViewSet):
    queryset = SolutionCategory.objects.all()
    serializer_class = SolutionCategorySerializer


class SolutionViewSet(viewsets.ModelViewSet):
    queryset = Solution.objects.all()
    serializer_class = SolutionSerializer


def index(request):
    casestudy_list = CaseStudy.objects.order_by('id')[:20]
    users = User.objects.order_by('id')[:20]
    context = {'casestudy_list': casestudy_list,
               'users': users,}
    
    context['graph1'] = Testgraph1().get_context_data()
    context['graph2'] = Testgraph2().get_context_data()
    return render(request, 'study_area/index.html', context)

def casestudy(request, casestudy_id):
    casestudy = CaseStudy.objects.get(pk=casestudy_id)
    stakeholder_categories = casestudy.stakeholdercategory_set.all()
    users = casestudy.user_set.all()

    context = {
        'casestudy': casestudy,
        'stakeholder_categories': stakeholder_categories,
        'users': users
    }
    return render(request, 'study_area/category.html', context)

def stakeholder_categories(request, stakeholder_category_id):
    stakeholder_category = StakeholderCategory.objects.get(
        pk=stakeholder_category_id)
    stakeholders = stakeholder_category.stakeholder_set.all()
    context = {'stakeholder_category': stakeholder_category,
               'stakeholders': stakeholders,
               }
    return render(request, 'changes/stakeholder_category.html', context)

def solutioncategories(request, solutioncategory_id):
    solution_category = SolutionCategory.objects.get(
        pk=solutioncategory_id)
    context = {'solution_category': solution_category,
               }
    return render(request, 'changes/solution_category.html', context)


def stakeholders(request, stakeholder_id):
    stakeholder = Stakeholder.objects.get(pk=stakeholder_id)
    if request.method == 'POST':
        form = NameForm(request.POST)
        if form.is_valid():
            stakeholder.name = form.cleaned_data['name']
            stakeholder.full_clean()
            stakeholder.save()
            return HttpResponseRedirect('/changes/stakeholdercategories/{}'.format(stakeholder.stakeholder_category.id))
    context = {'stakeholder': stakeholder,
               }
    return render(request, 'changes/stakeholder.html', context)

def implementations(request, implementation_id):
    implementation = Implementation.objects.get(pk=implementation_id)
    solutions = implementation.solutioninimplementation_set.all()

    context = {'implementation': implementation,
               'solutions': solutions,
               }
    return render(request, 'changes/implementation.html', context)

def solutions(request, solution_id):
    solution = Solution.objects.get(pk=solution_id)
    implementations = solution.implementation_set.all()
    print(implementations)
    context = {'solution': solution,
               }
    return render(request, 'changes/solution.html', context)

def solution_in_implematation(request, implementation_id, solution_id):
    sii = SolutionInImplementation.objects.get(
        implementation=implementation_id,
        solution=solution_id)
    geometries = sii.solutioninimplementationgeometry_set.all()
    quantities = sii.solutioninimplementationquantity_set.all()

    context = {'sii': sii,
               'geometries': geometries,
               'quantities': quantities,
               }
    return render(request, 'changes/solution_in_implementation.html', context)

def strategies(request, strategy_id):
    strategy = Strategy.objects.get(pk=strategy_id)
    implementations = strategy.implementations.all()

    context = {'strategy': strategy,
               'implementations': implementations,
               }
    return render(request, 'changes/strategy.html', context)

def user(request, user_id):
    user = User.objects.get(pk=user_id)
    context = {'user': user,
               }
    return render(request, 'changes/user.html', context)

def userincasestudy(request, user_id, casestudy_id):
    user = UserInCasestudy.objects.get(user_id=user_id,
                                       casestudy_id=casestudy_id)
    other_casestudies = user.user.casestudies.exclude(pk=casestudy_id).all
    context = {'user': user,
               'other_casestudies': other_casestudies,
               }
    return render(request, 'changes/user_in_casestudy.html', context)


from plotly.offline import plot
from plotly.graph_objs import (Scatter, Marker, Histogram2dContour, Contours,
                               Layout, Figure, Data)
from repair.apps.study_area.models import Links, Nodes
import numpy as np

class Testgraph1(TemplateView):
    template_name = 'graph.html'

    def get_context_data(self, **kwargs):
        context = super(Testgraph1, self).get_context_data(**kwargs)

        x = [-2,0,4,6,7]
        y = [q**2-q+3 for q in x]
        trace1 = Scatter(x=x, y=y, marker={'color': 'red', 'symbol': 104,
                                           'size': "10"},
                         mode="lines",  name='1st Trace')

        data=Data([trace1])
        layout=Layout(title=_("Plotly graph"), xaxis={'title':'x1'},
                      yaxis={'title':'x2'}, height=350)
        figure=Figure(data=data,layout=layout)
        div = plot(figure, auto_open=False, output_type='div', show_link=False)

        return div

class Testgraph2(TemplateView):

    def get_context_data(self, **kwargs):
        x = np.random.randn(2000)
        y = np.random.randn(2000)
        layout=Layout(title=_("Plotly Histogram"), height=350)
        figure=Figure(data=[
            Histogram2dContour(x=x, y=y, contours=Contours(coloring='heatmap')),
            Scatter(x=x, y=y, mode='markers', marker=Marker(
                color='white', size=3, opacity=0.3))], layout=layout)
        div = plot(figure, show_link=False, output_type='div')
        return div


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


from repair.apps.changes.forms import NameForm



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
    return render(request, 'changes/index.html', context)

def casestudy(request, casestudy_id):
    casestudy = CaseStudy.objects.get(pk=casestudy_id)
    stakeholder_categories = casestudy.stakeholdercategory_set.all()
    users = casestudy.user_set.all()
    solution_categories = casestudy.solution_categories

    context = {
        'casestudy': casestudy,
        'stakeholder_categories': stakeholder_categories,
        'users': users,
        'solution_categories': solution_categories,
               }
    return render(request, 'changes/casestudy.html', context)

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
    user = UserInCasestudy.objects.get(pk=user_id)
    implementations = user.implementation_set.all()
    solutions = user.solution_set.all()
    context = {'user': user,
               'implementations': implementations,
               'solutions': solutions,
               }
    return render(request, 'changes/user_in_casestudy.html', context)

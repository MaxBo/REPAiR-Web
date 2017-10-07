from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView
from django.shortcuts import render

from django.utils.translation import ugettext as _
from rest_framework import viewsets
from repair.apps.changes.models import (CaseStudy,
                                        Unit,
                                        UserAP12,
                                        UserAP34,
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
                                             )



class CaseStudyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = CaseStudy.objects.all()
    serializer_class = CaseStudySerializer


class StakeholderCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = StakeholderCategory.objects.all()
    serializer_class = StakeholderCategorySerializer


class StakeholderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Stakeholder.objects.all()
    serializer_class = StakeholderSerializer


def index(request):
    casestudy_list = CaseStudy.objects.order_by('id')[:10]
    context = {'casestudy_list': casestudy_list}
    return render(request, 'changes/index.html', context)

def casestudy(request, casestudy_id):
    casestudy = CaseStudy.objects.get(pk=casestudy_id)
    stakeholder_categories = casestudy.stakeholdercategory_set.all()
    users12 = casestudy.userap12_set.all()
    users34 = casestudy.userap34_set.all()
    solutions = casestudy.solution_set.all()

    context = {
        'casestudy': casestudy,
        'stakeholder_categories': stakeholder_categories,
        'users12': users12,
        'users34': users34,
        'solutions': solutions,
               }
    return render(request, 'changes/casestudy.html', context)

def stakeholder_categories(request, stakeholder_category_id):
    stakeholder_category = StakeholderCategory.objects.get(
        pk=stakeholder_category_id)
    stakeholders = stakeholder_category.stakeholder_set.all()
    context = {'stakeholder_category': stakeholder_category,
               'stakeholders': stakeholders,
               }
    return render(request, 'changes/stakeholders.html', context)

def stakeholders(request, stakeholder_id):
    stakeholder = Stakeholder.objects.get(pk=stakeholder_id)
    strategies = stakeholder.strategy_set.all()
    implementations = stakeholder.implementation_set.all()
    context = {'stakeholder': stakeholder,
               'strategies': strategies,
               'implementations':implementations,
               }
    return render(request, 'changes/stakeholder.html', context)

def implementations(request, implementation_id):
    implementation = Implementation.objects.get(pk=implementation_id)
    solutions = implementation.solutions.all()
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

def user12(request, user_id):
    user = UserAP12.objects.get(pk=user_id)
    solutions = user.solution_set.all()
    context = {'user': user,
               'solutions': solutions,
               }
    return render(request, 'changes/user.html', context)

def user34(request, user_id):
    user = UserAP34.objects.get(pk=user_id)
    implementations = user.implementation_set.all()
    context = {'user': user,
               'implementations': implementations,
               }
    return render(request, 'changes/user.html', context)

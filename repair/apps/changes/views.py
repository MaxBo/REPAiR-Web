from abc import ABC

from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404, JsonResponse
from django.template import loader
from django.views.generic import TemplateView
from django.shortcuts import render
import django.db.models
from django.shortcuts import get_object_or_404, get_list_or_404

from django.utils.translation import ugettext as _

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics


from repair.apps.login.views import OnlyCasestudyMixin, MultiSerializerViewSetMixin
from repair.apps.login.models import (CaseStudy, Profile, UserInCasestudy)
from repair.apps.changes.models import (
    Unit,
    SolutionCategory,
    Solution,
    Implementation,
    SolutionInImplementation,
    Strategy,
    )

from repair.apps.changes.serializers import (
    SolutionSerializer,
    SolutionCategorySerializer,
    SolutionPostSerializer,
    SolutionCategoryPostSerializer,
    ImplementationSerializer,
    SolutionInImplementationSerializer,
    )


from repair.apps.changes.forms import NameForm


def index(request):
    casestudy_list = CaseStudy.objects.order_by('id')[:20]
    users = Profile.objects.order_by('id')[:20]
    context = {'casestudy_list': casestudy_list,
               'users': users, }
    return render(request, 'changes/index.html', context)


def solutioncategories(request, solutioncategory_id):
    solution_category = SolutionCategory.objects.get(
        pk=solutioncategory_id)
    context = {'solution_category': solution_category,
               }
    return render(request, 'changes/solution_category.html', context)


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


# API Views


class SolutionCategoryViewSet(OnlyCasestudyMixin, viewsets.ModelViewSet):
    queryset = SolutionCategory.objects.all()
    serializer_class = SolutionCategorySerializer


class SolutionViewSet(OnlyCasestudyMixin, viewsets.ModelViewSet):
    serializer_class = SolutionSerializer
    queryset = Solution.objects.all()


class ImplementationViewSet(OnlyCasestudyMixin,
                            viewsets.ModelViewSet):
    serializer_class = ImplementationSerializer
    queryset = Implementation.objects.all()


class SolutionInImplementationViewSet(OnlyCasestudyMixin,
                                      viewsets.ModelViewSet):
    serializer_class = SolutionInImplementationSerializer
    queryset = SolutionInImplementation.objects.all()


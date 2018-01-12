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
from rest_framework import status, generics, mixins


from repair.apps.login.views import (CasestudyViewSetMixin,
                                     OnlySubsetMixin)
from repair.apps.login.models import (CaseStudy, Profile, UserInCasestudy)
from repair.views import BaseView
from repair.apps.changes.models import (
    Unit,
    SolutionCategory,
    Solution,
    Implementation,
    SolutionInImplementation,
    Strategy,
    SolutionQuantity,
    SolutionRatioOneUnit,
    SolutionInImplementationNote,
    SolutionInImplementationQuantity,
    SolutionInImplementationGeometry,

    )

from repair.apps.changes.serializers import (
    UnitSerializer,
    SolutionSerializer,
    SolutionCategorySerializer,
    ImplementationSerializer,
    SolutionInImplementationSerializer,
    SolutionQuantitySerializer,
    SolutionRatioOneUnitSerializer,
    SolutionInImplementationNoteSerializer,
    SolutionInImplementationQuantitySerializer,
    SolutionInImplementationGeometrySerializer,
    ImplementationOfUserSerializer,
    StrategySerializer,
    )


from repair.apps.changes.forms import NameForm


class ChangesIndexView(BaseView):
    def get(self, request):
        #casestudy_list = CaseStudy.objects.order_by('id')[:20]
        casestudy_list = self.casestudies()
        users = Profile.objects.order_by('id')[:20]
        context = {'casestudies': casestudy_list,
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


class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer


class SolutionCategoryViewSet(CasestudyViewSetMixin, viewsets.ModelViewSet):
    queryset = SolutionCategory.objects.all()
    serializer_class = SolutionCategorySerializer


class SolutionViewSet(CasestudyViewSetMixin, viewsets.ModelViewSet):
    serializer_class = SolutionSerializer
    queryset = Solution.objects.all()


class SolutionQuantityViewSet(CasestudyViewSetMixin, viewsets.ModelViewSet):
    serializer_class = SolutionQuantitySerializer
    queryset = SolutionQuantity.objects.all()


class SolutionRatioOneUnitViewSet(CasestudyViewSetMixin, viewsets.ModelViewSet):
    serializer_class = SolutionRatioOneUnitSerializer
    queryset = SolutionRatioOneUnit.objects.all()


class ImplementationViewSet(CasestudyViewSetMixin,
                            viewsets.ModelViewSet):
    serializer_class = ImplementationSerializer
    queryset = Implementation.objects.all()

class ImplementationOfUserViewSet(ImplementationViewSet):
    serializer_class = ImplementationOfUserSerializer


class StrategyViewset(CasestudyViewSetMixin, viewsets.ModelViewSet):
    serializer_class = StrategySerializer
    queryset = Strategy.objects.all()


class SolutionInImplementationViewSet(CasestudyViewSetMixin,
                                      viewsets.ModelViewSet):
    serializer_class = SolutionInImplementationSerializer
    queryset = SolutionInImplementation.objects.all()


class SolutionInImplementationNoteViewSet(CasestudyViewSetMixin,
                                      viewsets.ModelViewSet):
    serializer_class = SolutionInImplementationNoteSerializer
    queryset = SolutionInImplementationNote.objects.all()

class ReadUpdateViewSet(mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """
    A viewset that provides default `retrieve()`, `update()`,
    `partial_update()`,  and `list()` actions.
    No `create()` or `destroy()`
    """

class SolutionInImplementationQuantityViewSet(OnlySubsetMixin,
                                              ReadUpdateViewSet):
    """
    Has to provide exactly one quantity value
    for each quantity defined for the solution
    So no PUT or DELETE is allowed
    """
    serializer_class = SolutionInImplementationQuantitySerializer
    queryset = SolutionInImplementationQuantity.objects.all()


class SolutionInImplementationGeometryViewSet(CasestudyViewSetMixin,
                                      viewsets.ModelViewSet):
    serializer_class = SolutionInImplementationGeometrySerializer
    queryset = SolutionInImplementationGeometry.objects.all()


from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden

from repair.apps.login.models import UserInCasestudy
from repair.views import BaseView
from repair.apps.changes.models import (
    SolutionCategory,
    Solution,
    Implementation,
    SolutionInImplementation,
    Strategy,
    )


class ChangesIndexView(BaseView):
    def get(self, request, *args, **kwargs):
        casestudy_id = request.session.get('casestudy', 0)
        user = request.user

        try:
            uic = UserInCasestudy.objects.get(user__user_id=user.pk,
                                              casestudy_id=casestudy_id)
        except ObjectDoesNotExist:
            return HttpResponseForbidden(_('Please select a casestudy'))
        solution_list = Solution.objects.filter(
            user__casestudy=uic.casestudy_id)
        context = {'solution_list': solution_list,
                   'uic': uic,
                   }
        return render(request, 'changes/index.html', context)


def solutioncategories(request, solutioncategory_id):
    solution_category = SolutionCategory.objects.get(
        pk=solutioncategory_id)
    context = {'solution_category': solution_category,
               }
    return render(request, 'changes/solution_category.html', context)


def implementations(request, implementation_id):
    implementation = Implementation.objects.get(pk=implementation_id)
    sii = implementation.solutioninimplementation_set.all()

    context = {'implementation': implementation,
               'solutions': sii,
               }
    return render(request, 'changes/implementation.html', context)


def solutions(request, solution_id):
    solution = Solution.objects.get(pk=solution_id)
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
    impl_in_strategiy = strategy.implementations.all()

    context = {'strategy': strategy,
               'implementations': impl_in_strategiy,
               }
    return render(request, 'changes/strategy.html', context)


from django.shortcuts import render



from repair.apps.login.models import Profile
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

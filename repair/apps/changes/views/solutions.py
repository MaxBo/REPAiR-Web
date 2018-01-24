from repair.apps.login.views import CasestudyViewSetMixin

from repair.apps.changes.models import (
    Unit,
    SolutionCategory,
    Solution,
    SolutionQuantity,
    SolutionRatioOneUnit,
    )

from repair.apps.changes.serializers import (
    UnitSerializer,
    SolutionSerializer,
    SolutionCategorySerializer,
    SolutionQuantitySerializer,
    SolutionRatioOneUnitSerializer,
    )

from repair.apps.utils.views import ModelPermissionViewSet


class UnitViewSet(ModelPermissionViewSet):
    add_perm = 'changes.add_unit'
    change_perm = 'changes.change_unit'
    delete_perm = 'changes.delete_unit'
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer


class SolutionCategoryViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    add_perm = 'changes.add_solutioncategory'
    change_perm = 'changes.change_solutioncategory'
    delete_perm = 'changes.delete_solutioncategory'
    queryset = SolutionCategory.objects.all()
    serializer_class = SolutionCategorySerializer


class SolutionViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    add_perm = 'changes.add_solution'
    change_perm = 'changes.change_solution'
    delete_perm = 'changes.delete_solution'
    serializer_class = SolutionSerializer
    queryset = Solution.objects.all()


class SolutionQuantityViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    add_perm = 'changes.add_solutionquantity'
    change_perm = 'changes.change_solutionquantity'
    delete_perm = 'changes.delete_solutionquantity'
    serializer_class = SolutionQuantitySerializer
    queryset = SolutionQuantity.objects.all()


class SolutionRatioOneUnitViewSet(CasestudyViewSetMixin,
                                  ModelPermissionViewSet):
    add_perm = 'changes.add_solutionratiooneunit'
    change_perm = 'changes.change_solutionratiooneunit'
    delete_perm = 'changes.delete_solutionratiooneunit'
    serializer_class = SolutionRatioOneUnitSerializer
    queryset = SolutionRatioOneUnit.objects.all()

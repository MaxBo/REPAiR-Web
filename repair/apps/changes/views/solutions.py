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

from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet)


class UnitViewSet(ModelPermissionViewSet):
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    pagination_class = None


class SolutionCategoryViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    queryset = SolutionCategory.objects.all()
    serializer_class = SolutionCategorySerializer


class SolutionViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    serializer_class = SolutionSerializer
    queryset = Solution.objects.all()


class SolutionQuantityViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    serializer_class = SolutionQuantitySerializer
    queryset = SolutionQuantity.objects.all()


class SolutionRatioOneUnitViewSet(CasestudyViewSetMixin,
                                  ModelPermissionViewSet):
    serializer_class = SolutionRatioOneUnitSerializer
    queryset = SolutionRatioOneUnit.objects.all()

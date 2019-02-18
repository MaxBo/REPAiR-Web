from repair.apps.changes.models import (
    SolutionCategory,
    Solution,
    ImplementationQuestion,
    )

from repair.apps.changes.serializers import (
    SolutionSerializer,
    SolutionCategorySerializer,
    ImplementationQuestionSerializer,
    )

from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet)


class SolutionCategoryViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    queryset = SolutionCategory.objects.all()
    serializer_class = SolutionCategorySerializer


class SolutionViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    serializer_class = SolutionSerializer
    queryset = Solution.objects.all()


class ImplementationQuestionViewSet(CasestudyViewSetMixin,
                                    ModelPermissionViewSet):
    serializer_class = ImplementationQuestionSerializer
    queryset = ImplementationQuestion.objects.all()



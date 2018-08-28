from repair.apps.utils.views import CasestudyViewSetMixin, ReadUpdateViewSet
from repair.apps.changes.models import (
    Strategy,
    SolutionInStrategy,
    SolutionInStrategyQuantity,
    )

from repair.apps.changes.serializers import (
    StrategySerializer,
    SolutionInStrategySerializer,
    SolutionInStrategyQuantitySerializer,
    )

from repair.apps.utils.views import (ModelPermissionViewSet,
                                     ReadUpdatePermissionViewSet)


class StrategyViewSet(CasestudyViewSetMixin,
                      ModelPermissionViewSet):
    serializer_class = StrategySerializer
    queryset = Strategy.objects.all()

    def list(self, request, *args, **kwargs):

        if (request.user.id and 'user' not in request.query_params and
            'user__in' not in request.query_params):
            self.queryset = self.queryset.filter(user__user__user_id=request.user.id)

        return super().list(request, *args, **kwargs)


class SolutionInStrategyViewSet(CasestudyViewSetMixin,
                                ModelPermissionViewSet):
    serializer_class = SolutionInStrategySerializer
    queryset = SolutionInStrategy.objects.all()


class SolutionInStrategyQuantityViewSet(CasestudyViewSetMixin,
                                        ReadUpdatePermissionViewSet):
    """
    Has to provide exactly one quantity value
    for each quantity defined for the solution
    So no PUT or DELETE is allowed
    """
    serializer_class = SolutionInStrategyQuantitySerializer
    queryset = SolutionInStrategyQuantity.objects.all()

from repair.apps.utils.views import CasestudyViewSetMixin, ReadUpdateViewSet
from repair.apps.asmfa.models import KeyflowInCasestudy
from repair.apps.login.models import UserInCasestudy
from repair.apps.changes.models import (
    Strategy,
    SolutionInStrategy,
    ImplementationQuantity,
    SolutionPart
    )

from repair.apps.changes.serializers import (
    StrategySerializer,
    SolutionInStrategySerializer,
    ImplementationQuantitySerializer,
    SolutionPartSerializer
    )

from repair.apps.utils.views import (ModelPermissionViewSet,
                                     ReadUpdatePermissionViewSet)


class StrategyViewSet(CasestudyViewSetMixin,
                      ModelPermissionViewSet):
    serializer_class = StrategySerializer
    queryset = Strategy.objects.all()

    def get_queryset(self):
        strategies = Strategy.objects.all()
        casestudy_pk = self.kwargs.get('casestudy_pk')
        keyflow_pk = self.kwargs.get('keyflow_pk')
        if keyflow_pk is not None:
            strategies = strategies.filter(keyflow__id=keyflow_pk)
        # if no requested specific user strategies
        # only retrieve strategies of user
        if (self.request.user.id and 'user' not in self.request.query_params and
            'user__in' not in self.request.query_params):
            strategies = strategies.filter(
                user__user__user_id=self.request.user.id)
            # there should always be at least one strategy per user and keyflow
            # (actually exactly one, but this should be handled by the frontend)
            if len(strategies) == 0 and keyflow_pk is not None:
                profile = UserInCasestudy.objects.get(
                    user=self.request.user.id,
                    casestudy=casestudy_pk
                )
                keyflow = KeyflowInCasestudy.objects.get(id=keyflow_pk)
                strategy = Strategy(
                    user=profile,
                    keyflow=keyflow,
                    name=''
                )
                strategy.save()
                strategies = Strategy.objects.filter(id=strategy.id)
        return strategies


class SolutionInStrategyViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    serializer_class = SolutionInStrategySerializer
    queryset = SolutionInStrategy.objects.all()



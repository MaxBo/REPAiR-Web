from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponseNotFound
from django.utils.translation import gettext as _

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
from repair.apps.asmfa.graphs.graph import StrategyGraph


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

    @action(methods=['get', 'post'], detail=True)
    def build_graph(self, request, **kwargs):
        strategy = self.get_object()
        sgraph = StrategyGraph(strategy)
        try:
            graph = sgraph.build()
        except FileNotFoundError:
            return HttpResponseNotFound(_(
                'The base data is not set up. '
                'Please contact your workshop leader.'))
        serializer = self.get_serializer(strategy)
        return Response(serializer.data)

class SolutionInStrategyViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    serializer_class = SolutionInStrategySerializer
    queryset = SolutionInStrategy.objects.all()


class ImplementationQuantityViewSet(CasestudyViewSetMixin,
                                    ReadUpdatePermissionViewSet):
    """
    Has to provide exactly one quantity value
    for each quantity defined for the solution
    So no PUT or DELETE is allowed
    """
    serializer_class = ImplementationQuantitySerializer
    queryset = ImplementationQuantity.objects.all()


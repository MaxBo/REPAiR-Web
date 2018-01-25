from repair.apps.login.views import CasestudyViewSetMixin
from repair.apps.changes.models import Strategy
from repair.apps.changes.serializers import StrategySerializer
from repair.apps.utils.views import ModelPermissionViewSet


class StrategyViewset(CasestudyViewSetMixin, ModelPermissionViewSet):
    serializer_class = StrategySerializer
    queryset = Strategy.objects.all()

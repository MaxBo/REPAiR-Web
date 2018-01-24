# API View
from reversion.views import RevisionMixin

from repair.apps.asmfa.models import (
    GroupStock,
    ActivityStock,
    ActorStock,
)

from repair.apps.asmfa.serializers import (
    GroupStockSerializer,
    ActivityStockSerializer,
    ActorStockSerializer,
)

from repair.apps.login.views import CasestudyViewSetMixin
from repair.apps.utils.views import ModelPermissionViewSet


class GroupStockViewSet(RevisionMixin,
                        CasestudyViewSetMixin,
                        ModelPermissionViewSet):
    add_perm = 'asmfa.add_groupstock'
    change_perm = 'asmfa.change_groupstock'
    delete_perm = 'asmfa.delete_groupstock'
    queryset = GroupStock.objects.all()
    serializer_class = GroupStockSerializer


class ActivityStockViewSet(RevisionMixin,
                           CasestudyViewSetMixin,
                           ModelPermissionViewSet):
    add_perm = 'asmfa.add_activitystock'
    change_perm = 'asmfa.change_activitystock'
    delete_perm = 'asmfa.delete_activitystock'
    queryset = ActivityStock.objects.all()
    serializer_class = ActivityStockSerializer


class ActorStockViewSet(RevisionMixin,
                        CasestudyViewSetMixin,
                        ModelPermissionViewSet):
    add_perm = 'asmfa.add_actorstock'
    change_perm = 'asmfa.change_actorstock'
    delete_perm = 'asmfa.delete_actorstock'
    queryset = ActorStock.objects.all()
    serializer_class = ActorStockSerializer
    additional_filters = {'origin__included': True}

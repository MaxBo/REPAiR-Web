# API View
from reversion.views import RevisionMixin

from repair.apps.asmfa.models import (
    ActivityGroup,
    Activity,
    Actor, )

from repair.apps.asmfa.serializers import (
    ActivityGroupSerializer,
    ActivitySerializer,
    ActorSerializer,
    ActivityListSerializer,
    ActorListSerializer,
    ActivityGroupListSerializer
)

from repair.apps.asmfa.views import UnlimitedResultsSetPagination

from repair.apps.login.views import CasestudyViewSetMixin
from repair.apps.utils.views import ModelPermissionViewSet


class ActivityGroupViewSet(RevisionMixin, CasestudyViewSetMixin,
                           ModelPermissionViewSet):
    add_perm = 'asmfa.add_activitygroup'
    change_perm = 'asmfa.change_activitygroup'
    delete_perm = 'asmfa.delete_activitygroup'
    serializer_class = ActivityGroupSerializer
    queryset = ActivityGroup.objects.order_by('id')
    serializers = {'list': ActivityGroupListSerializer}


class ActivityViewSet(RevisionMixin, CasestudyViewSetMixin,
                      ModelPermissionViewSet):
    add_perm = 'asmfa.add_activity'
    change_perm = 'asmfa.change_activity'
    delete_perm = 'asmfa.delete_activity'
    serializer_class = ActivitySerializer
    queryset = Activity.objects.order_by('id')
    serializers = {'list': ActivityListSerializer}


class ActorViewSet(RevisionMixin, CasestudyViewSetMixin,
                   ModelPermissionViewSet):
    pagination_class = UnlimitedResultsSetPagination
    add_perm = 'asmfa.add_actor'
    change_perm = 'asmfa.change_actor'
    delete_perm = 'asmfa.delete_actor'
    serializer_class = ActorSerializer
    queryset = Actor.objects.order_by('id')
    serializers = {'list': ActorListSerializer}
    
    def get_queryset(self):
        return Actor.objects.select_related(
            "activity__activitygroup").order_by('id')


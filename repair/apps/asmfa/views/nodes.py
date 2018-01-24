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
    AllActivitySerializer,
    AllActorSerializer,
    AllActorListSerializer,
)

from repair.apps.login.views import CasestudyViewSetMixin
from repair.apps.utils.views import ModelPermissionViewSet


class ActivityGroupViewSet(RevisionMixin, CasestudyViewSetMixin,
                           ModelPermissionViewSet):
    add_perm = 'asmfa.add_activitygroup'
    change_perm = 'asmfa.change_activitygroup'
    delete_perm = 'asmfa.delete_activitygroup'
    serializer_class = ActivityGroupSerializer
    queryset = ActivityGroup.objects.all()


class ActivityViewSet(RevisionMixin, CasestudyViewSetMixin,
                      ModelPermissionViewSet):
    add_perm = 'asmfa.add_activity'
    change_perm = 'asmfa.change_activity'
    delete_perm = 'asmfa.delete_activity'
    serializer_class = ActivitySerializer
    queryset = Activity.objects.all()


class ActorViewSet(RevisionMixin, CasestudyViewSetMixin,
                   ModelPermissionViewSet):
    add_perm = 'asmfa.add_actor'
    change_perm = 'asmfa.change_actor'
    delete_perm = 'asmfa.delete_actor'
    serializer_class = ActorSerializer
    queryset = Actor.objects.all()


class AllActivityViewSet(ActivityViewSet):
    serializer_class = AllActivitySerializer


class AllActorViewSet(ActorViewSet):
    serializer_class = AllActorSerializer
    serializers = {'list': AllActorListSerializer, }

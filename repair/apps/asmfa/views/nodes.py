# API View
from reversion.views import RevisionMixin
from django.contrib.gis.geos import GEOSGeometry

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
    pagination_class = UnlimitedResultsSetPagination
    add_perm = 'asmfa.add_activitygroup'
    change_perm = 'asmfa.change_activitygroup'
    delete_perm = 'asmfa.delete_activitygroup'
    serializer_class = ActivityGroupSerializer
    queryset = ActivityGroup.objects.order_by('id')
    serializers = {'list': ActivityGroupListSerializer}
    
    def get_queryset(self):
        groups = ActivityGroup.objects
        keyflow_pk = self.kwargs.get('keyflow_pk')
        if keyflow_pk is not None:
            groups = groups.filter(keyflow__id=keyflow_pk)
        return groups.order_by('id')


class ActivityViewSet(RevisionMixin, CasestudyViewSetMixin,
                      ModelPermissionViewSet):
    pagination_class = UnlimitedResultsSetPagination
    add_perm = 'asmfa.add_activity'
    change_perm = 'asmfa.change_activity'
    delete_perm = 'asmfa.delete_activity'
    serializer_class = ActivitySerializer
    queryset = Activity.objects.order_by('id')
    serializers = {'list': ActivityListSerializer}
    
    def get_queryset(self):
        activities = Activity.objects.\
            select_related("activitygroup")
        keyflow_pk = self.kwargs.get('keyflow_pk')
        if keyflow_pk is not None:
            activities = activities.filter(activitygroup__keyflow__id=keyflow_pk)
        return activities.order_by('id')


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
        actors = Actor.objects.\
            select_related("activity__activitygroup").\
            prefetch_related('administrative_location')
        keyflow_pk = self.kwargs.get('keyflow_pk')
        if keyflow_pk is not None:
            actors = actors.filter(activity__activitygroup__keyflow__id=keyflow_pk)
            
        return actors.order_by('id')


class FilterActorViewSet(ActorViewSet):
    
    def create(self, request, **kwargs):
        return super().list(request, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        if 'id' in self.request.data:
            ids = self.request.data['id'].split(",")
            queryset = queryset.filter(id__in=ids)
        if 'area' in self.request.data:
            geojson = self.request.data['area']
            poly = GEOSGeometry(geojson)
            queryset = queryset.filter(
                administrative_location__geom__intersects=poly)
        return queryset
    
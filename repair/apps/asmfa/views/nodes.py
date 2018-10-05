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

from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet,
                                     PostGetViewMixin)


class ActivityGroupViewSet(PostGetViewMixin, RevisionMixin, CasestudyViewSetMixin,
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
        if (self.isGET):
            if 'id' in self.request.data:
                ids = self.request.data['id'].split(",")
                groups = groups.filter(id__in=ids)
        return groups.order_by('id')


class ActivityViewSet(PostGetViewMixin, RevisionMixin, CasestudyViewSetMixin,
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
            select_related("activitygroup__keyflow__casestudy").defer(
                "activitygroup__keyflow__note",
                "activitygroup__keyflow__casestudy__geom",
                "activitygroup__keyflow__casestudy__focusarea")
        keyflow_pk = self.kwargs.get('keyflow_pk')
        if keyflow_pk is not None:
            activities = activities.filter(activitygroup__keyflow__id=keyflow_pk)
        if (self.isGET):
            if 'id' in self.request.data:
                ids = self.request.data['id'].split(",")
                activities = activities.filter(id__in=ids)
        return activities.order_by('id')


class ActorViewSet(PostGetViewMixin, RevisionMixin, CasestudyViewSetMixin,
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
            select_related("activity__activitygroup__keyflow__casestudy").\
            prefetch_related('administrative_location').defer(
                "activity__activitygroup__keyflow__note",
                "activity__activitygroup__keyflow__casestudy__geom",
                "activity__activitygroup__keyflow__casestudy__focusarea")
        keyflow_pk = self.kwargs.get('keyflow_pk')
        if keyflow_pk is not None:
            actors = actors.filter(
                activity__activitygroup__keyflow__id=keyflow_pk)

        if (self.isGET):
            if 'id' in self.request.data:
                ids = self.request.data['id'].split(",")
                actors = actors.filter(id__in=ids)
            if 'area' in self.request.data:
                geojson = self.request.data['area']
                poly = GEOSGeometry(geojson)
                actors = actors.filter(
                    administrative_location__geom__intersects=poly)

        return actors.order_by('id')

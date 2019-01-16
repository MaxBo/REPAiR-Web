# API View
from reversion.views import RevisionMixin
from repair.apps.asmfa.views import UnlimitedResultsSetPagination

from repair.apps.asmfa.models import (
    OperationalLocation,
    AdministrativeLocation,
)

from repair.apps.asmfa.serializers import (
    AdministrativeLocationSerializer,
    OperationalLocationSerializer,
    AdministrativeLocationOfActorSerializer,
    OperationalLocationsOfActorSerializer,
    AdminLocationCreateSerializer
)

from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet,
                                     PostGetViewMixin)


class AdministrativeLocationViewSet(PostGetViewMixin, RevisionMixin,
                                    CasestudyViewSetMixin,
                                    ModelPermissionViewSet):
    pagination_class = UnlimitedResultsSetPagination
    add_perm = 'asmfa.add_administrativelocation'
    change_perm = 'asmfa.change_administrativelocation'
    delete_perm = 'asmfa.delete_administrativelocation'
    queryset = AdministrativeLocation.objects.all()
    serializer_class = AdministrativeLocationSerializer
    serializers = {
        'list': AdministrativeLocationSerializer,
        'create': AdminLocationCreateSerializer
    }

    def get_queryset(self):
        locations = AdministrativeLocation.objects.select_related(
            "actor__activity__activitygroup__keyflow__casestudy").all().defer(
                "actor__activity__activitygroup__keyflow__note",
                "actor__activity__activitygroup__keyflow__casestudy__geom",
                "actor__activity__activitygroup__keyflow__casestudy__focusarea")
        if (self.isGET):
            if 'actor__in' in self.request.data:
                ids = self.request.data['actor__in'].split(",")
                locations = locations.filter(actor__in=ids)
        return locations.order_by('id')


class OperationalLocationViewSet(PostGetViewMixin, RevisionMixin,
                                 CasestudyViewSetMixin,
                                 ModelPermissionViewSet):
    pagination_class = UnlimitedResultsSetPagination
    add_perm = 'asmfa.add_operationallocation'
    change_perm = 'asmfa.change_operationallocation'
    delete_perm = 'asmfa.delete_operationallocation'
    queryset = OperationalLocation.objects.all()
    serializer_class = OperationalLocationSerializer

    def get_queryset(self):
        locations = OperationalLocation.objects.select_related(
            "actor__activity__activitygroup__keyflow__casestudy").all().defer(
                "actor__activity__activitygroup__keyflow__note",
                "actor__activity__activitygroup__keyflow__casestudy__geom",
                "actor__activity__activitygroup__keyflow__casestudy__focusarea")
        if (self.isGET):
            if 'actor__in' in self.request.data:
                ids = self.request.data['actor__in'].split(",")
                locations = locations.filter(actor__in=ids)
        return locations.order_by('id')


class AdministrativeLocationOfActorViewSet(PostGetViewMixin, RevisionMixin,
                                           CasestudyViewSetMixin,
                                           ModelPermissionViewSet):
    pagination_class = UnlimitedResultsSetPagination
    queryset = AdministrativeLocation.objects.all()
    serializer_class = AdministrativeLocationOfActorSerializer

    def get_queryset(self):
        locations = AdministrativeLocation.objects.select_related(
            "actor__activity__activitygroup__keyflow__casestudy").all().defer(
                "actor__activity__activitygroup__keyflow__note",
                "actor__activity__activitygroup__keyflow__casestudy__geom",
                "actor__activity__activitygroup__keyflow__casestudy__focusarea")
        if (self.isGET):
            if 'actor__in' in self.request.data:
                ids = self.request.data['actor__in'].split(",")
                locations = locations.filter(actor__in=ids)
        return locations.order_by('id')


class OperationalLocationsOfActorViewSet(PostGetViewMixin, RevisionMixin,
                                         CasestudyViewSetMixin,
                                         ModelPermissionViewSet):
    pagination_class = UnlimitedResultsSetPagination
    queryset = OperationalLocation.objects.all()
    serializer_class = OperationalLocationsOfActorSerializer

    def get_queryset(self):
        locations = OperationalLocation.objects.select_related(
            "actor__activity__activitygroup__keyflow__casestudy").all().defer(
                "actor__activity__activitygroup__keyflow__note",
                "actor__activity__activitygroup__keyflow__casestudy__geom",
                "actor__activity__activitygroup__keyflow__casestudy__focusarea")
        if (self.isGET):
            if 'actor__in' in self.request.data:
                ids = self.request.data['actor__in'].split(",")
                locations = locations.filter(actor__in=ids)
        return locations.order_by('id')


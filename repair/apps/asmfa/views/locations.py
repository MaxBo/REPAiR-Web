# API View
from reversion.views import RevisionMixin

from repair.apps.asmfa.models import (
    OperationalLocation,
    AdministrativeLocation,
)

from repair.apps.asmfa.serializers import (
    AdministrativeLocationSerializer,
    OperationalLocationSerializer,
    AdministrativeLocationOfActorSerializer,
    OperationalLocationsOfActorSerializer,
)

from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet)


class AdministrativeLocationViewSet(RevisionMixin, CasestudyViewSetMixin,
                                    ModelPermissionViewSet):
    add_perm = 'asmfa.add_administrativelocation'
    change_perm = 'asmfa.change_administrativelocation'
    delete_perm = 'asmfa.delete_administrativelocation'
    queryset = AdministrativeLocation.objects.all()
    serializer_class = AdministrativeLocationSerializer
    
    def get_queryset(self):
        return AdministrativeLocation.objects.select_related(
            "actor__activity__activitygroup__keyflow__casestudy").all()


class OperationalLocationViewSet(RevisionMixin, CasestudyViewSetMixin,
                                 ModelPermissionViewSet):
    add_perm = 'asmfa.add_operationallocation'
    change_perm = 'asmfa.change_operationallocation'
    delete_perm = 'asmfa.delete_operationallocation'
    queryset = OperationalLocation.objects.all()
    serializer_class = OperationalLocationSerializer
    
    def get_queryset(self):
        return OperationalLocation.objects.select_related(
            "actor__activity__activitygroup__keyflow__casestudy").all()


class AdministrativeLocationOfActorViewSet(RevisionMixin,
                                           CasestudyViewSetMixin,
                                           ModelPermissionViewSet):
    queryset = AdministrativeLocation.objects.all()
    serializer_class = AdministrativeLocationOfActorSerializer
    
    def get_queryset(self):
        return AdministrativeLocation.objects.select_related(
            "actor__activity__activitygroup__keyflow__casestudy").all()


class OperationalLocationsOfActorViewSet(RevisionMixin, CasestudyViewSetMixin,
                                         ModelPermissionViewSet):
    queryset = OperationalLocation.objects.all()
    serializer_class = OperationalLocationsOfActorSerializer
    
    def get_queryset(self):
        return OperationalLocation.objects.select_related(
            "actor__activity__activitygroup__keyflow__casestudy").all()

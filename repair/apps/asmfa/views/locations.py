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

from repair.apps.login.views import CasestudyViewSetMixin
from repair.apps.utils.views import ModelPermissionViewSet


class AdministrativeLocationViewSet(RevisionMixin, CasestudyViewSetMixin,
                                    ModelPermissionViewSet):
    add_perm = 'asmfa.add_administrativelocation'
    change_perm = 'asmfa.change_administrativelocation'
    delete_perm = 'asmfa.delete_administrativelocation'
    queryset = AdministrativeLocation.objects.all()
    serializer_class = AdministrativeLocationSerializer


class OperationalLocationViewSet(RevisionMixin, CasestudyViewSetMixin,
                                 ModelPermissionViewSet):
    add_perm = 'asmfa.add_operationallocation'
    change_perm = 'asmfa.change_operationallocation'
    delete_perm = 'asmfa.delete_operationallocation'
    queryset = OperationalLocation.objects.all()
    serializer_class = OperationalLocationSerializer


class AdministrativeLocationOfActorViewSet(RevisionMixin,
                                           CasestudyViewSetMixin,
                                           ModelPermissionViewSet):
    queryset = AdministrativeLocation.objects.all()
    serializer_class = AdministrativeLocationOfActorSerializer


class OperationalLocationsOfActorViewSet(RevisionMixin, CasestudyViewSetMixin,
                                         ModelPermissionViewSet):
    queryset = OperationalLocation.objects.all()
    serializer_class = OperationalLocationsOfActorSerializer

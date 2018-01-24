# API View
from abc import ABC

from rest_framework.viewsets import ModelViewSet
from reversion.views import RevisionMixin

from repair.apps.asmfa.models import (
    ActivityGroup,
    Activity,
    Actor,
    Flow,
    Activity2Activity,
    Actor2Actor,
    Group2Group,
    Keyflow,
    KeyflowInCasestudy,
    GroupStock,
    ActivityStock,
    ActorStock,
    OperationalLocation,
    AdministrativeLocation,
    Product,
    Material,
)

from repair.apps.asmfa.serializers import (
    ActivityGroupSerializer,
    ActivitySerializer,
    ActorSerializer,
    FlowSerializer,
    Actor2ActorSerializer,
    Activity2ActivitySerializer,
    Group2GroupSerializer,
    KeyflowSerializer,
    KeyflowInCasestudySerializer,
    KeyflowInCasestudyPostSerializer,
    GroupStockSerializer,
    ActivityStockSerializer,
    ActorStockSerializer,
    AllActivitySerializer,
    AllActorSerializer,
    AdministrativeLocationSerializer,
    OperationalLocationSerializer,
    AdministrativeLocationOfActorSerializer,
    AdministrativeLocationOfActorPostSerializer,
    OperationalLocationsOfActorSerializer,
    AllActorListSerializer,
    ProductSerializer,
    MaterialSerializer,
)

from repair.apps.login.views import CasestudyViewSetMixin
from repair.apps.utils.views import ModelPermissionViewSet

class ActivityGroupViewSet(RevisionMixin, CasestudyViewSetMixin,
                           ModelPermissionViewSet):
    serializer_class = ActivityGroupSerializer
    queryset = ActivityGroup.objects.all()


class ActivityViewSet(RevisionMixin, CasestudyViewSetMixin,
                      ModelPermissionViewSet):
    serializer_class = ActivitySerializer
    queryset = Activity.objects.all()


class ActorViewSet(RevisionMixin, CasestudyViewSetMixin,
                   ModelPermissionViewSet):
    serializer_class = ActorSerializer
    queryset = Actor.objects.all()


class AllActivityViewSet(ActivityViewSet):
    serializer_class = AllActivitySerializer


class AllActorViewSet(ActorViewSet):
    serializer_class = AllActorSerializer
    serializers = {'list': AllActorListSerializer,}


class KeyflowViewSet(ModelPermissionViewSet):
    queryset = Keyflow.objects.all()
    serializer_class = KeyflowSerializer


class KeyflowInCasestudyViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    """
    API endpoint that allows Keyflowincasestudy to be viewed or edited.
    """
    queryset = KeyflowInCasestudy.objects.all()
    serializer_class = KeyflowInCasestudySerializer
    serializers = {'create': KeyflowInCasestudyPostSerializer,
                   'update': KeyflowInCasestudyPostSerializer,}


class GroupStockViewSet(RevisionMixin,
                        CasestudyViewSetMixin,
                        ModelPermissionViewSet):
    queryset = GroupStock.objects.all()
    serializer_class = GroupStockSerializer


class ActivityStockViewSet(RevisionMixin,
                           CasestudyViewSetMixin,
                           ModelPermissionViewSet):
    queryset = ActivityStock.objects.all()
    serializer_class = ActivityStockSerializer


class ActorStockViewSet(RevisionMixin,
                        CasestudyViewSetMixin,
                        ModelPermissionViewSet):
    queryset = ActorStock.objects.all()
    serializer_class = ActorStockSerializer
    additional_filters = {'origin__included': True}


class FlowViewSet(RevisionMixin,
                  CasestudyViewSetMixin,
                  ModelPermissionViewSet,
                  ABC):
    """
    Abstract BaseClass for a FlowViewSet
    The Subclass has to provide a model inheriting from Flow
    and a serializer-class inheriting form and a model
    """
    serializer_class = FlowSerializer
    model = Flow


class Group2GroupViewSet(FlowViewSet):
    queryset = Group2Group.objects.all()
    serializer_class = Group2GroupSerializer


class Activity2ActivityViewSet(FlowViewSet):
    queryset = Activity2Activity.objects.all()
    serializer_class = Activity2ActivitySerializer


class Actor2ActorViewSet(FlowViewSet):
    queryset = Actor2Actor.objects.all()
    serializer_class = Actor2ActorSerializer
    additional_filters = {'origin__included': True,
                          'destination__included': True}


class AdministrativeLocationViewSet(RevisionMixin, CasestudyViewSetMixin,
                                    ModelPermissionViewSet):
    queryset = AdministrativeLocation.objects.all()
    serializer_class = AdministrativeLocationSerializer
    #serializers = {'create': AdministrativeLocationOfActorPostSerializer}


class OperationalLocationViewSet(RevisionMixin, CasestudyViewSetMixin,
                                 ModelPermissionViewSet):
    queryset = OperationalLocation.objects.all()
    serializer_class = OperationalLocationSerializer


class AdministrativeLocationOfActorViewSet(RevisionMixin, CasestudyViewSetMixin,
                                           ModelPermissionViewSet):
    queryset = AdministrativeLocation.objects.all()
    serializer_class = AdministrativeLocationOfActorSerializer


class OperationalLocationsOfActorViewSet(RevisionMixin, CasestudyViewSetMixin,
                                         ModelPermissionViewSet):
    queryset = OperationalLocation.objects.all()
    serializer_class = OperationalLocationsOfActorSerializer


class ProductViewSet(RevisionMixin, CasestudyViewSetMixin,
                     ModelPermissionViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class MaterialViewSet(RevisionMixin, CasestudyViewSetMixin,
                      ModelPermissionViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer

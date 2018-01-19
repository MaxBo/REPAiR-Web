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

from repair.apps.login.views import CasestudyViewSetMixin, OnlySubsetMixin
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
    serializers = {'list': AllActorListSerializer,}


class KeyflowViewSet(ModelPermissionViewSet):
    add_perm = 'asmfa.add_keyflow'
    change_perm = 'asmfa.change_keyflow'
    delete_perm = 'asmfa.delete_keyflow'
    queryset = Keyflow.objects.all()
    serializer_class = KeyflowSerializer


class KeyflowInCasestudyViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    """
    API endpoint that allows Keyflowincasestudy to be viewed or edited.
    """
    add_perm = 'asmfa.add_keyflowincasestudy'
    change_perm = 'asmfa.change_keyflowincasestudy'
    delete_perm = 'asmfa.delete_keyflowincasestudy'
    queryset = KeyflowInCasestudy.objects.all()
    serializer_class = KeyflowInCasestudySerializer
    serializers = {'create': KeyflowInCasestudyPostSerializer,
                   'update': KeyflowInCasestudyPostSerializer,}


class GroupStockViewSet(RevisionMixin, OnlySubsetMixin,
                        ModelPermissionViewSet):
    add_perm = 'asmfa.add_groupstock'
    change_perm = 'asmfa.change_groupstock'
    delete_perm = 'asmfa.delete_groupstock'
    queryset = GroupStock.objects.all()
    serializer_class = GroupStockSerializer


class ActivityStockViewSet(RevisionMixin, OnlySubsetMixin,
                           ModelPermissionViewSet):
    add_perm = 'asmfa.add_activitystock'
    change_perm = 'asmfa.change_activitystock'
    delete_perm = 'asmfa.delete_activitystock'
    queryset = ActivityStock.objects.all()
    serializer_class = ActivityStockSerializer


class ActorStockViewSet(RevisionMixin, OnlySubsetMixin,
                        ModelPermissionViewSet):
    add_perm = 'asmfa.add_actorstock'
    change_perm = 'asmfa.change_actorstock'
    delete_perm = 'asmfa.delete_actorstock'
    queryset = ActorStock.objects.all()
    serializer_class = ActorStockSerializer
    additional_filters = {'origin__included': True}


class FlowViewSet(RevisionMixin, OnlySubsetMixin, ModelPermissionViewSet, ABC):
    """
    Abstract BaseClass for a FlowViewSet
    The Subclass has to provide a model inheriting from Flow
    and a serializer-class inheriting form and a model
    """
    serializer_class = FlowSerializer
    model = Flow


class Group2GroupViewSet(FlowViewSet):
    add_perm = 'asmfa.add_group2group'
    change_perm = 'asmfa.change_group2group'
    delete_perm = 'asmfa.delete_group2group'
    queryset = Group2Group.objects.all()
    serializer_class = Group2GroupSerializer


class Activity2ActivityViewSet(FlowViewSet):
    add_perm = 'asmfa.add_activity2activity'
    change_perm = 'asmfa.change_activity2activity'
    delete_perm = 'asmfa.delete_activity2activity'
    queryset = Activity2Activity.objects.all()
    serializer_class = Activity2ActivitySerializer


class Actor2ActorViewSet(FlowViewSet):
    add_perm = 'asmfa.add_actor2actor'
    change_perm = 'asmfa.change_actor2actor'
    delete_perm = 'asmfa.delete_actor2actor'
    queryset = Actor2Actor.objects.all()
    serializer_class = Actor2ActorSerializer
    additional_filters = {'origin__included': True,
                          'destination__included': True}


class AdministrativeLocationViewSet(RevisionMixin, CasestudyViewSetMixin,
                                    ModelPermissionViewSet):
    add_perm = 'asmfa.add_administrativelocation'
    change_perm = 'asmfa.change_administrativelocation'
    delete_perm = 'asmfa.delete_administrativelocation'
    queryset = AdministrativeLocation.objects.all()
    serializer_class = AdministrativeLocationSerializer
    #serializers = {'create': AdministrativeLocationOfActorPostSerializer}


class OperationalLocationViewSet(RevisionMixin, CasestudyViewSetMixin,
                                 ModelPermissionViewSet):
    add_perm = 'asmfa.add_operationallocation'
    change_perm = 'asmfa.change_operationallocation'
    delete_perm = 'asmfa.delete_operationallocation'
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
    add_perm = 'asmfa.add_product'
    change_perm = 'asmfa.change_product'
    delete_perm = 'asmfa.delete_product'
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class MaterialViewSet(RevisionMixin, CasestudyViewSetMixin,
                      ModelPermissionViewSet):
    add_perm = 'asmfa.add_material'
    change_perm = 'asmfa.change_material'
    delete_perm = 'asmfa.delete_material'
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer

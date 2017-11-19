# API View
from abc import ABC

from rest_framework.viewsets import ModelViewSet

from repair.apps.asmfa.models import (
    ActivityGroup,
    Activity,
    Actor,
    Flow,
    Activity2Activity,
    Actor2Actor,
    Group2Group,
    Material,
    Quality,
    MaterialInCasestudy,
    GroupStock,
    ActivityStock,
    ActorStock,
    OperationalLocation,
    AdministrativeLocation,
)

from repair.apps.asmfa.serializers import (
    ActivityGroupSerializer,
    ActivitySerializer,
    ActorSerializer,
    FlowSerializer,
    Actor2ActorSerializer,
    Activity2ActivitySerializer,
    Group2GroupSerializer,
    MaterialSerializer,
    QualitySerializer,
    MaterialInCasestudySerializer,
    GroupStockSerializer,
    ActivityStockSerializer,
    ActorStockSerializer,
    AllActivitySerializer,
    AllActorSerializer,
    AdministrativeLocationSerializer,
    OperationalLocationSerializer,
    AdministrativeLocationOfActorSerializer,
    OperationalLocationsOfActorSerializer,
)

from repair.apps.login.views import ViewSetMixin, OnlySubsetMixin


class ActivityGroupViewSet(ViewSetMixin, ModelViewSet):
    serializer_class = ActivityGroupSerializer
    queryset = ActivityGroup.objects.all()


class ActivityViewSet(ViewSetMixin, ModelViewSet):
    serializer_class = ActivitySerializer
    queryset = Activity.objects.all()


class ActorViewSet(ViewSetMixin, ModelViewSet):
    serializer_class = ActorSerializer
    queryset = Actor.objects.all()


class AllActivityViewSet(ActivityViewSet):
    serializer_class = AllActivitySerializer


class AllActorViewSet(ActorViewSet):
    serializer_class = AllActorSerializer


class MaterialViewSet(ViewSetMixin, ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer


class QualityViewSet(ViewSetMixin, ModelViewSet):
    queryset = Quality.objects.all()
    serializer_class = QualitySerializer
    casestudy_only = False


class MaterialInCasestudyViewSet(ViewSetMixin, ModelViewSet):
    """
    API endpoint that allows materialincasestudy to be viewed or edited.
    """
    queryset = MaterialInCasestudy.objects.all()
    serializer_class = MaterialInCasestudySerializer


class GroupStockViewSet(OnlySubsetMixin, ModelViewSet):
    queryset = GroupStock.objects.all()
    serializer_class = GroupStockSerializer


class ActivityStockViewSet(OnlySubsetMixin, ModelViewSet):
    queryset = ActivityStock.objects.all()
    serializer_class = ActivityStockSerializer


class ActorStockViewSet(OnlySubsetMixin, ModelViewSet):
    queryset = ActorStock.objects.all()
    serializer_class = ActorStockSerializer
    additional_filters = {'origin__included': True}


class FlowViewSet(OnlySubsetMixin, ModelViewSet, ABC):
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


class AdministrativeLocationViewSet(ViewSetMixin, ModelViewSet):
    queryset = AdministrativeLocation.objects.all()
    serializer_class = AdministrativeLocationSerializer


class OperationalLocationViewSet(ViewSetMixin, ModelViewSet):
    queryset = OperationalLocation.objects.all()
    serializer_class = OperationalLocationSerializer


class AdministrativeLocationOfActorViewSet(ViewSetMixin, ModelViewSet):
    queryset = AdministrativeLocation.objects.all()
    serializer_class = AdministrativeLocationOfActorSerializer


class OperationalLocationsOfActorViewSet(ViewSetMixin, ModelViewSet):
    queryset = OperationalLocation.objects.all()
    serializer_class = OperationalLocationsOfActorSerializer

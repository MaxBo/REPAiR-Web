# API View
from abc import ABC
from repair.apps.asmfa.views import UnlimitedResultsSetPagination

from rest_framework.viewsets import ModelViewSet
from reversion.views import RevisionMixin

from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet,
                                     PostGetViewMixin)


from repair.apps.asmfa.models import (
    Reason,
    Flow,
    AdministrativeLocation,
    Activity2Activity,
    Actor2Actor,
    Group2Group,
    Material,
    Composition,
    ProductFraction,
    Actor,
    Activity,
    ActivityGroup,
    ActorStock,
    GroupStock,
    ActivityStock,
    Process
)

from repair.apps.studyarea.models import (
    Area, AdminLevels
)

from repair.apps.asmfa.serializers import (
    ReasonSerializer,
    FlowSerializer,
    Actor2ActorSerializer,
    Activity2ActivitySerializer,
    Group2GroupSerializer,
    Actor2ActorCreateSerializer,
    GroupStockSerializer,
    ActorStockSerializer,
    ActivityStockSerializer,
    ActorStockCreateSerializer,
    ProcessSerializer
)


class ReasonViewSet(RevisionMixin, ModelViewSet):
    pagination_class = None
    serializer_class = ReasonSerializer
    queryset = Reason.objects.all()


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
    pagination_class = UnlimitedResultsSetPagination


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


class Actor2ActorViewSet(PostGetViewMixin, FlowViewSet):
    add_perm = 'asmfa.add_actor2actor'
    change_perm = 'asmfa.change_actor2actor'
    delete_perm = 'asmfa.delete_actor2actor'
    queryset = Actor2Actor.objects.all()
    serializer_class = Actor2ActorSerializer
    serializers = {
        'list': Actor2ActorSerializer,
        'create': Actor2ActorCreateSerializer,
    }
    additional_filters = {'origin__included': True,
                          'destination__included': True}


class StockViewSet(RevisionMixin,
                   CasestudyViewSetMixin,
                   ModelPermissionViewSet,
                   ABC):
    pagination_class = UnlimitedResultsSetPagination

    def get_queryset(self):
        model = self.serializer_class.Meta.model
        return model.objects.\
               select_related('keyflow__casestudy').\
               select_related('publication').\
               select_related("origin").\
               prefetch_related("composition__fractions").\
               all().defer(
                "keyflow__note",
                "keyflow__casestudy__geom",
                "keyflow__casestudy__focusarea").\
               order_by('id')


class GroupStockViewSet(StockViewSet):
    add_perm = 'asmfa.add_groupstock'
    change_perm = 'asmfa.change_groupstock'
    delete_perm = 'asmfa.delete_groupstock'
    queryset = GroupStock.objects.all()
    serializer_class = GroupStockSerializer


class ActivityStockViewSet(StockViewSet):
    add_perm = 'asmfa.add_activitystock'
    change_perm = 'asmfa.change_activitystock'
    delete_perm = 'asmfa.delete_activitystock'
    queryset = ActivityStock.objects.all()
    serializer_class = ActivityStockSerializer


class ActorStockViewSet(PostGetViewMixin, StockViewSet):
    add_perm = 'asmfa.add_actorstock'
    change_perm = 'asmfa.change_actorstock'
    delete_perm = 'asmfa.delete_actorstock'
    queryset = ActorStock.objects.all()
    serializer_class = ActorStockSerializer
    serializers = {
        'list': ActorStockSerializer,
        'create': ActorStockCreateSerializer,
    }
    additional_filters = {'origin__included': True}


class ProcessViewSet(ModelViewSet):
    queryset = Process.objects.all()
    serializer_class = ProcessSerializer

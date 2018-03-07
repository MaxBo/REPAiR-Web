# API View
from abc import ABC

from rest_framework.viewsets import ModelViewSet
from reversion.views import RevisionMixin
from rest_framework.response import Response
from django.db.models import Q

from repair.apps.asmfa.models import (
    Reason,
    Flow,
    Activity2Activity,
    Actor2Actor,
    Group2Group,
    Material,
    Composition,
    ProductFraction
)

from repair.apps.asmfa.serializers import (
    ReasonSerializer,
    FlowSerializer,
    Actor2ActorSerializer,
    Activity2ActivitySerializer,
    Group2GroupSerializer,
)

from repair.apps.login.views import CasestudyViewSetMixin
from repair.apps.utils.views import ModelPermissionViewSet


class ReasonViewSet(RevisionMixin, ModelViewSet):
    pagination_class = None
    serializer_class = ReasonSerializer
    queryset = Reason.objects.all()


def filter_by_material(material, queryset):
    """filter queryset by their compositions,
    their fractions have to contain the given material or children
    of the material"""
    # get the children of the given material
    materials = material.children
    # fractions have to contain any of given material or its children
    materials.append(material)
    fractions = ProductFraction.objects.filter(material__in=materials)
    # the compositions containing the filtered fractions
    compositions = fractions.values('composition')
    # the flows containing the filtered compositions
    filtered = queryset.filter(composition__in=compositions)
    return filtered


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
    
    def list(self, request, **kwargs):
        self.check_permission(request, 'view')
        SerializerClass = self.get_serializer_class()
        query_params = request.query_params
        filtered = None
        if 'material' in query_params.keys():
            try:
                material = Material.objects.get(id=query_params['material'])
            except Material.DoesNotExist:
                return Response(status=404)
            filtered = filter_by_material(material, self.queryset)
        if 'node' in query_params.keys():
            queryset = filtered or self.queryset
            nodes = query_params['node']
            filtered = queryset.filter(Q(origin__in=nodes) |
                                       Q(destination__in=nodes))
        if filtered:
            serializer = SerializerClass(filtered, many=True,
                                         context={'request': request, })
            return Response(serializer.data)
        return super().list(request, **kwargs)


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

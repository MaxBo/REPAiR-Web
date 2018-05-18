# API View
from abc import ABC

from rest_framework.viewsets import ModelViewSet
from reversion.views import RevisionMixin
from rest_framework.response import Response
from django.db.models import Q
import time
from collections import defaultdict, OrderedDict

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
    materials = material.descendants
    # fractions have to contain children and the material itself
    materials.append(material)
    fractions = ProductFraction.objects.filter(material__in=materials)
    # the compositions containing the filtered fractions
    compositions = fractions.values('composition')
    # the flows containing the filtered compositions
    filtered = queryset.filter(composition__in=compositions)
    return filtered

#def aggregate_compositions(material, queryset):
    #children = material.children
    #for flow in queryset:
        #flow.composition.aggregate_by_materials(children)
    #return queryset

# in place changing data
def aggregate_compositions(materials, data):
    desc_dict = {}
    for mat in materials: desc_dict[mat] = {}
    for serialized_flow in data:
        composition = serialized_flow['composition']
        if not composition:
            continue
        old_total = serialized_flow['amount']
        new_total = 0
        aggregation = defaultdict.fromkeys(materials, 0)
        for serialized_fraction in composition['fractions']:
            for child_material in materials:
                child_dict = desc_dict[child_material]
                mat_id = serialized_fraction['material']
                is_desc = child_dict.get(mat_id)
                if is_desc is None:
                    fraction_material = Material.objects.get(
                        id=serialized_fraction['material'])
                    child_dict[mat_id] = is_desc = fraction_material.is_descendant(child_material)
                if is_desc:
                    amount = serialized_fraction['fraction'] * old_total
                    aggregation[child_material] += amount
                    new_total += amount
        
        aggregated_fractions = []
        
        for child_material, amount in aggregation.items():
            if amount > 0:
                aggregated_fraction = OrderedDict({
                    'material': child_material.id,
                    'fraction': amount / new_total,
                })
                aggregated_fractions.append(aggregated_fraction)
        serialized_flow['amount'] = new_total
        composition['fractions'] = aggregated_fractions


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
        queryset = self.get_queryset()
        material = None
        filtered = False

        if 'waste' in query_params.keys():
            queryset = queryset.filter(waste=query_params.get('waste'))
            filtered = True

        if 'nodes' in query_params.keys() or 'nodes[]' in query_params.keys():
            nodes = (query_params.get('nodes', None)
                     or request.GET.getlist('nodes[]')) 
            queryset = queryset.filter(Q(origin__in=nodes) |
                                       Q(destination__in=nodes))
            filtered = True

        if 'from' in query_params.keys() or 'from[]' in query_params.keys():
            nodes = (query_params.get('from', None)
                     or request.GET.getlist('from[]')) 
            queryset = queryset.filter(origin__in=nodes)
            filtered = True

        if 'to' in query_params.keys() or 'to[]' in query_params.keys():
            nodes = (query_params.get('to', None)
                     or request.GET.getlist('to[]')) 
            queryset = queryset.filter(destination__in=nodes)
            filtered = True

        if 'material' in query_params.keys():
            try:
                material = Material.objects.get(id=query_params['material'])
            except Material.DoesNotExist:
                return Response(status=404)
            queryset = filter_by_material(material, queryset)
            filtered = True
        
        if ('aggregated' in query_params.keys() and
            query_params['aggregated'] in ['true', 'True']):
            serializer = SerializerClass(queryset, many=True,
                                         context={'request': request, })
            
            t = time.time()
            data = serializer.data
            print(time.time() - t)
            # material was requested (see if clause 'material') -> 
            # aggregate compositions by the direct children
            if material:
                materials = material.children
            # no material was requested -> aggregate by top level materials
            else:
                materials = Material.objects.filter(parent__isnull=True)
            t = time.time()
            aggregate_compositions(materials, data)
            print(time.time() - t)
            return Response(data)

        if filtered:
            serializer = SerializerClass(queryset, many=True,
                                         context={'request': request, })
            return Response(serializer.data)
        return super().list(request, **kwargs)

    def get_queryset(self):
        model = self.serializer_class.Meta.model
        return model.objects.\
               select_related('keyflow__casestudy').\
               select_related('publication').\
               select_related("origin").\
               select_related("destination").\
               prefetch_related("composition__fractions").\
               all()


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
    
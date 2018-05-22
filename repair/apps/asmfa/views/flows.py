# API View
from abc import ABC

from rest_framework.viewsets import ModelViewSet
from reversion.views import RevisionMixin
from rest_framework.response import Response
from django.db.models import Q
import time
import numpy as np
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
def process_data_fractions(materials, data, aggregate=False):
    desc_dict = {}
    # dictionary to store requested materials and if other materials are
    # descendants of those (including the material itself), much faster than
    # repeatedly getting the materials and their ancestors
    for mat in materials:
        desc_dict[mat] = { mat.id: True }
    for serialized_flow in data:
        composition = serialized_flow['composition']
        if not composition:
            continue
        old_total = serialized_flow['amount']
        new_total = 0
        aggregated_amounts = defaultdict.fromkeys(materials, 0)
        
        # remove fractions that are no descendants of the material
        valid_fractions = []
        for serialized_fraction in composition['fractions']:
            for material in materials:
                child_dict = desc_dict[material]
                fraction_mat_id = serialized_fraction['material']
                is_desc = child_dict.get(fraction_mat_id)
                # save time by doing this once and storing it
                if is_desc is None:
                    fraction_material = Material.objects.get(
                        id=serialized_fraction['material'])
                    child_dict[fraction_mat_id] = is_desc = fraction_material.is_descendant(material)
                if is_desc:
                    amount = serialized_fraction['fraction'] * old_total
                    aggregated_amounts[material] += amount
                    new_total += amount
                    valid_fractions.append(serialized_fraction)

        new_fractions = []
        # aggregation: new fraction for each material
        if aggregate:
            for material, amount in aggregated_amounts.items():
                if amount > 0:
                    aggregated_fraction = OrderedDict({
                        'material': material.id,
                        'fraction': amount / new_total,
                    })
                    new_fractions.append(aggregated_fraction)
                
        # no aggregation: keep the fractions whose materials are descendants 
        # (->valid) and recalculate the fraction values
        else:
            for fraction in valid_fractions:
                if new_total > 0:
                    fraction['fraction'] = fraction['fraction'] * old_total / new_total
                # old amount might be zero -> can't calc. fractions with that
                else:
                    fraction['fraction'] = 0
                new_fractions.append(fraction)
        serialized_flow['amount'] = new_total
        composition['fractions'] = new_fractions

# inplace aggregate queryset (DOESN'T WORK, because the serializer is unable 
# to get the new fractions in reverse)
def aggregate_queryset(materials, queryset):
    from django.db.models import IntegerField, Case, When, Value, Sum
    args = []
    mat_dict = {}
    t = time.time()
    for mat in materials:
        all_mats = mat.descendants
        all_mats.append(mat)
        mat_ids = tuple(m.id for m in all_mats)
        w = When(material_id__in = mat_ids, then=Value(mat.id))
        args.append(w)
        mat_dict[mat.id] = mat
    
    for flow in queryset:
        fractions = ProductFraction.objects.filter(composition=flow.composition)
        an = fractions.annotate(ancestor=Case(*args, default=-1,
                                              output_field=IntegerField()))
        agg = an.values('ancestor').annotate(Sum('fraction'))
        new_comp = Composition(name='aggregated')
        for s in agg:
            mat_id = s['ancestor']
            if mat_id < 0:
                continue
            new_fraction = ProductFraction(composition=new_comp,
                                           material=mat_dict[mat_id])
        flow.composition = new_comp


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
        
        filter_waste = 'waste' in query_params.keys()
        filter_nodes = ('nodes' in query_params.keys() or
                        'nodes[]' in query_params.keys())
        filter_from = ('from' in query_params.keys() or
                       'from[]' in query_params.keys())
        filter_to = ('to' in query_params.keys() or
                     'to[]' in query_params.keys())
        filter_material = 'material' in query_params.keys()
        aggregate = ('aggregated' in query_params.keys() and
                     query_params['aggregated'] in ['true', 'True'])
        
        # do the filtering and serializing of superclass, if none of the above
        # filters are queried (unfortunately they all conflict with filters of 
        # superclass CasestudyViewSetMixin)
        if not np.any([filter_waste, filter_nodes, filter_from, filter_to,
                       filter_material, aggregate]):
            return super().list(request, **kwargs)
    
        # filter products (waste=False) or waste (waste=True)
        if filter_waste:
            queryset = queryset.filter(waste=query_params.get('waste'))
        
        # filter by origins AND destinations
        if filter_nodes:
            nodes = (query_params.get('nodes', None)
                     or request.GET.getlist('nodes[]')) 
            queryset = queryset.filter(Q(origin__in=nodes) |
                                       Q(destination__in=nodes))
        
        # filter by origins
        if filter_from:
            nodes = (query_params.get('from', None)
                     or request.GET.getlist('from[]')) 
            queryset = queryset.filter(origin__in=nodes)

        # filter by destinations
        if filter_to:
            nodes = (query_params.get('to', None)
                     or request.GET.getlist('to[]')) 
            queryset = queryset.filter(destination__in=nodes)

        # filter the flows by their fractions excluding flows whose
        # fractions don't contain the requested material (incl. child materials)
        if filter_material:
            try:
                material = Material.objects.get(id=query_params['material'])
            except Material.DoesNotExist:
                return Response(status=404)
            queryset = filter_by_material(material, queryset)
        
        serializer = SerializerClass(queryset, many=True,
                                         context={'request': request, })
        data = serializer.data
    
        # if the fractions of flows are filtered by material, the other
        # fractions should be removed from the returned data
        if filter_material and not aggregate:
            process_data_fractions([material], data, aggregate=False)
            return Response(data)
    
        # aggregate the fractions of the queryset
        if aggregate:
            # take the material and its children from if-clause 'filter_material'
            if material:
                materials = [material] + list(material.children)
            # no material was requested -> aggregate by top level materials
            if material is None:
                materials = Material.objects.filter(parent__isnull=True)
            
            #aggregate_queryset(materials, queryset)
            #filtered = True

            process_data_fractions(materials, data, aggregate=True)
            return Response(data)

        return Response(data)

    def get_queryset(self):
        model = self.serializer_class.Meta.model
        flows = model.objects.\
                select_related('keyflow__casestudy').\
                select_related('publication').\
                select_related("origin").\
                select_related("destination").\
                prefetch_related("composition__fractions").\
                all()
    
        keyflow_pk = self.kwargs.get('keyflow_pk')
        if keyflow_pk is not None:
            flows = flows.filter(keyflow__id=keyflow_pk)
        return flows


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
    
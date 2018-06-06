# API View
from abc import ABC

from rest_framework.viewsets import ModelViewSet
from reversion.views import RevisionMixin
from rest_framework.response import Response
from django.db.models import Q, Sum
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
    ProductFraction,
    Actor, 
    Activity,
    ActivityGroup, 
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
def process_data_fractions(material, childmaterials, data, aggregate=False):
    desc_dict = {}
    # dictionary to store requested materials and if other materials are
    # descendants of those (including the material itself), much faster than
    # repeatedly getting the materials and their ancestors
    for mat in childmaterials:
        desc_dict[mat] = { mat.id: True }
    for serialized_flow in data:
        composition = serialized_flow['composition']
        if not composition:
            continue
        old_total = serialized_flow['amount']
        new_total = 0
        aggregated_amounts = defaultdict.fromkeys(childmaterials, 0)
        if material:
            aggregated_amounts[material] = 0
        
        # remove fractions that are no descendants of the material
        valid_fractions = []
        for serialized_fraction in composition['fractions']:
            if material and material.id == serialized_fraction['material']:
                aggregated_amounts[material] += (
                    serialized_fraction['fraction'] * old_total)
                valid_fractions.append(serialized_fraction)
                continue
            for child in childmaterials:
                child_dict = desc_dict[child]
                fraction_mat_id = serialized_fraction['material']
                is_desc = child_dict.get(fraction_mat_id)
                # save time by doing this once and storing it
                if is_desc is None:
                    fraction_material = Material.objects.get(
                        id=serialized_fraction['material'])
                    child_dict[fraction_mat_id] = is_desc = fraction_material.is_descendant(child)
                if is_desc:
                    amount = serialized_fraction['fraction'] * old_total
                    aggregated_amounts[child] += amount
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
        aggregation_level = query_params.get('aggregation_level', None)
        
        # do the filtering and serializing of superclass, if none of the above
        # filters are queried (unfortunately they all conflict with filters of 
        # superclass CasestudyViewSetMixin)
        if not np.any([filter_waste,
                       filter_nodes,
                       filter_from,
                       filter_to,
                       filter_material,
                       aggregate,
                       aggregation_level is not None]):
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
        
        data = self.aggregate_to_level(aggregation_level, data, queryset)
        
        # if the fractions of flows are filtered by material, the other
        # fractions should be removed from the returned data
        if filter_material and not aggregate:
            process_data_fractions(material, material.children,
                                   data, aggregate=False)
            return Response(data)
    
        # aggregate the fractions of the queryset
        if aggregate:
            # take the material and its children from if-clause 'filter_material'
            if material:
                childmaterials = material.children
            # no material was requested -> aggregate by top level materials
            if material is None:
                childmaterials = Material.objects.filter(parent__isnull=True)
            
            #aggregate_queryset(materials, queryset)
            #filtered = True

            process_data_fractions(material, childmaterials, data, aggregate=True)
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

    def aggregate_to_level(self, aggregation_level, data, queryset):
        """
        Aggregate actor level to the according flow level
        if not implemented in the subclass, do nothing
        """
        if aggregation_level.lower() == 'activity':
            actors_activity = dict(Actor.objects.values_list('id', 'activity'))
            acts = queryset.values_list('origin__activity',
                                        'destination__activity')

        elif aggregation_level.lower() == 'activitygroup':
            actors_activity = dict(Actor.objects.values_list(
                'id', 'activity__activitygroup'))
            acts = queryset.values_list(
                'origin__activity__activitygroup',
                'destination__activity__activitygroup')
        else:
            return data

        act2act_amounts = acts.annotate(Sum('amount'))
        custom_compositions = dict()
        total_amounts = dict()
        act2act_id = -1
        new_flows = list()
        for origin, destination, amount in act2act_amounts:
            key = (origin, destination)
            total_amounts[key] = amount
            custom_compositions[key] = OrderedDict(id=act2act_id,
                                                   name='custom',
                                                   nace='custom nace',
                                                   masses_of_materials=OrderedDict(), 
                                                   )
            act2act_id -= 1

        for serialized_flow in data:
            amount = serialized_flow['amount']
            composition = serialized_flow['composition']
            if not composition:
                continue
            key = (actors_activity[serialized_flow['origin']],
                   actors_activity[serialized_flow['destination']])
            custom_composition = custom_compositions[key]
            masses_of_materials = custom_composition['masses_of_materials']
    
            fractions = composition['fractions']
            for fraction in fractions:
                mass = amount * fraction['fraction']
                material = fraction['material']
                mass_of_material = masses_of_materials.get(material, 0) + mass
                masses_of_materials[material] = mass_of_material
        
        for origin, destination, amount in act2act_amounts:
            key = (origin, destination)
            custom_composition = custom_compositions[key]
            masses_of_materials = custom_composition['masses_of_materials']
            fractions = list()
            for material, mass_of_material in masses_of_materials.items():
                fraction = mass_of_material / amount
                fraction_ordered_dict = OrderedDict({
                        'material': material,
                        'fraction': fraction,
                    })
                fractions.append(fraction_ordered_dict)
            custom_composition['fractions'] = fractions
            del(custom_composition['masses_of_materials'])
            
            new_flow = OrderedDict(id=custom_composition['id'],
                                   amount=amount,
                                   composition=custom_composition,
                                   origin=origin,
                                   destination=destination)
            new_flows.append(new_flow)
        return new_flows

        
    def aggregate2activitiygroups(self, data):
        """"""
        

class Group2GroupViewSet(FlowViewSet):
    add_perm = 'asmfa.add_group2group'
    change_perm = 'asmfa.change_group2group'
    delete_perm = 'asmfa.delete_group2group'
    queryset = Group2Group.objects.all()
    serializer_class = Group2GroupSerializer

    def aggregate_to_my_level(self, data):
        """
        Aggregate actor level to the activity group level
        """

        
class Activity2ActivityViewSet(FlowViewSet):
    add_perm = 'asmfa.add_activity2activity'
    change_perm = 'asmfa.change_activity2activity'
    delete_perm = 'asmfa.delete_activity2activity'
    queryset = Activity2Activity.objects.all()
    serializer_class = Activity2ActivitySerializer
    
    def aggregate_to_my_level(self, data):
        """
        Aggregate actor level to the activity level
        """


class Actor2ActorViewSet(FlowViewSet):
    add_perm = 'asmfa.add_actor2actor'
    change_perm = 'asmfa.change_actor2actor'
    delete_perm = 'asmfa.delete_actor2actor'
    queryset = Actor2Actor.objects.all()
    serializer_class = Actor2ActorSerializer
    additional_filters = {'origin__included': True,
                          'destination__included': True}
    
    
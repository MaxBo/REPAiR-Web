# API View
from abc import ABC

from rest_framework.viewsets import ModelViewSet
from reversion.views import RevisionMixin
from rest_framework.response import Response
from django.db.models import Q, Subquery, Min, IntegerField, OuterRef
import time
import numpy as np
import copy
import json
from collections import defaultdict, OrderedDict

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
    Actor, Activity, ActivityGroup
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

# in place changing data
def process_data_fractions(material, childmaterials, data,
                           aggregate_materials=False):
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
        if aggregate_materials:
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


class FilterActor2ActorViewSet(Actor2ActorViewSet):
    '''
    body params:
    body = {
        waste: true / false,  # products or waste, don't pass for both
        
        # filter by origin/destination actors
        actors: {
            direction: "to" / "from" / "both", # return flows to or from given actors
            ids = [...] # ids of the actors, all others are excluded
        },
        # filter/aggregate by given material 
        material: {
            aggregate: true / false, # aggregate child materials
                                     # to level of given material
                                     # or to top level if no id is given
            id: id, # id of material
        },
        
        # aggregate origin/dest. actors belonging to given
        # activity/groupon spatial level, child nodes have
        # to be exclusively 'activity's or 'activitygroup's
        spatial: {  
            activity: {
                id: id,  # id of activitygroup/activity
                level: id,  # id of spatial level (as in AdminLevels)
            },
        }
    }
    '''
    # structure of serialized components of a flow as the serializer
    # will return it
    flow_struct = OrderedDict(id=None,
                              amount=0,
                              composition=None,
                              origin=None,
                              destination=None,
                              origin_level=None,
                              destination_level=None,
                              )

    composition_struct = OrderedDict(id=None,
                                     name='custom',
                                     nace='custom',
                                     fractions=[],
                                     )

    fractions_struct = OrderedDict(material=None,
                                   fraction=0
                                   )

    # POST is used to send filter parameters not to create
    def create(self, request, **kwargs):
        self.check_permission(request, 'view')
        SerializerClass = self.get_serializer_class()
        params = request.data
        queryset = self.get_queryset()
        material = None

        waste_filter = params.get('waste', None)
        actor_filter = params.get('actors', None)
        material_filter = params.get('material', None)
        spatial_aggregation = params.get('spatial', None)

        # filter products (waste=False) or waste (waste=True)
        if waste_filter is not None:
            queryset = queryset.filter(waste=waste_filter)

        # filter by origins/destinations and direction
        if actor_filter:
            actors = actor_filter.get('ids', None)
            direction = actor_filter.get('direction', 'both')
            if direction == 'from':
                queryset = queryset.filter(origin__in=actors)
            elif direction == 'to':
                queryset = queryset.filter(destination__in=actors)
            else:
                queryset = queryset.filter(Q(origin__in=actors) |
                                           Q(destination__in=actors))

        # filter the flows by their fractions excluding flows whose
        # fractions don't contain the requested material (incl. child materials)
        if material_filter and 'id' in material_filter.keys():
            try:
                material = Material.objects.get(id=material_filter['id'])
            except Material.DoesNotExist:
                return Response(status=404)
            queryset = filter_by_material(material, queryset)

        serializer = SerializerClass(queryset, many=True,
                                         context={'request': request, })
        data = serializer.data

        if spatial_aggregation:
            spatj = json.loads(spatial_aggregation)
            levels = {}
            types = []
            for node_type, values in spatj.items():
                node_id = values['id']
                level_id = values['level']
                levels[node_id] = level_id
                types.append(node_type)
            unique_types = np.unique(types)
            # ToDo: raise HTTP malformed request 
            if len(unique_types) != 1:
                raise Exception('only one type allowed at the same type')
            typ = unique_types[0]
            if typ == 'activity':
                group_relation = 'activity'
            elif typ == 'activitygroup':
                group_relation = 'activity__activitygroup'
            else:
                raise Exception('unknown type')
            data = self.spatial_aggregation(data, queryset,
                                            group_relation, levels)
        
        # POSTPROCESSING: all following operations are performed on serialized
        # data
        
        if material_filter:
            aggregate_materials = material_filter.get('aggregate', False)
            # if the fractions of flows are filtered by material, the other
            # fractions should be removed from the returned data
            if not aggregate_materials:
                process_data_fractions(material, material.children,
                                       data, aggregate_materials=False)
                return Response(data)

            # aggregate the fractions of the queryset
            # take the material and its children from if-clause 'filter_material'
            if material:
                childmaterials = material.children
            # no material was requested -> aggregate by top level materials
            if material is None:
                childmaterials = Material.objects.filter(parent__isnull=True)

            #aggregate_queryset(materials, queryset)
            #filtered = True

            process_data_fractions(material, childmaterials, data,
                                   aggregate_materials=True)
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

    def spatial_aggregation(self, data, queryset, group_relation, levels):
        '''
        aggregate the serialized flows when origins/destinations belong to
        specific group_relation ('activity' or 'activity__activitygroup')
        levels is a dict of ids of activity resp. activitygroup and the id of
        the administrative level whose areas the actors of those activity/
        activitygroup should be mapped to
        '''
        mapped_to_area = []
        
        actor_ids = list(queryset.values_list('origin_id', 'destination_id'))
        actor_ids = [t for s in actor_ids for t in s]
        actors = Actor.objects.filter(id__in=actor_ids)
        
        # prepare map of ids, actors are mapped to themselves by default 
        # (indicated by level None)
        id_map = dict(zip(actor_ids, actor_ids))
        # keep track of level of area
        area_levels = {}
        
        # map the actors belonging to given activities or groups to 
        # areas of given levels
        for rid, level in levels.items():
            # actors in given relation (activity or activitygroup)
            actors_in_relation = actors.filter(**{group_relation: rid})
            locations = AdministrativeLocation.objects.filter(
                actor__in=actors_in_relation)
            
            # mark actors that should be mapped to area but have no location
            air_ids = [x[0] for x in actors_in_relation.values_list('id')]
            mapped_to_area = dict(zip(air_ids, [None] * len(air_ids)))
            
            annotated = self.add_area(locations, level)
            mapped_to_area.update(dict(
                annotated.values_list('actor_id', 'adminarea_id')))
            # overwrite id mapping for actors mapped to an area
            id_map.update(dict(mapped_to_area))
            area_set= set(mapped_to_area.values())
            area_levels.update(dict(zip(area_set, [level] * len(area_set))))

        # aggregate by mapped origins/destinations
        aggregated_amounts = {}
        for flow in data:
            origin = flow['origin']
            destination = flow['destination']
            mapped_origin = id_map.get(origin, None)
            mapped_destination = id_map.get(destination, None)
            # origin or destination could not be located inside any area ->
            # ignore it (won't be included in the results)
            if mapped_origin is None or mapped_destination is None:
                continue
            amount = flow['amount']
            composition = flow['composition']
            key = (mapped_origin, mapped_destination)
            if key not in aggregated_amounts:
                aggregated_amounts[key] = {
                    'amount': 0,
                    'fractions': defaultdict(lambda: 0)
                }
            aggregation = aggregated_amounts[key]
            aggregation['amount'] += amount
            for fraction in composition['fractions']:
                material = fraction['material']
                mass = fraction['fraction'] * amount
                aggregation['fractions'][material] += mass

        # create new serialized flows based on aggregated amounts
        new_flows = []
        for (origin, destination), aggregation in aggregated_amounts.items():
            new_flow = self.flow_struct.copy()
            new_flows.append(new_flow)
            amount = aggregation['amount']
            new_flow['amount'] = aggregation['amount']
            new_comp = copy.deepcopy(self.composition_struct)
            new_flow['composition'] = new_comp
            new_flow['origin'] = origin
            new_flow['destination'] = destination
            origin_level = area_levels.get(origin, None)
            destination_level = area_levels.get(destination, None)
            new_flow['origin_level'] = origin_level
            new_flow['destination_level'] = destination_level
            for material, mass in aggregation['fractions'].items():
                new_fract = self.fractions_struct.copy()
                new_fract['material'] = material
                new_amount = 0 if amount == 0 else mass / amount
                new_fract['fraction'] = new_amount
                new_comp['fractions'].append(new_fract)

        return new_flows

    def add_area(self, locations, level):
        '''
        annotate given locations with the ids of the areas ('adminarea_id')
        of given administrative level they are located in,
        adminarea_id will be None if a location is not located in any of the areas
        '''
        areas = Area.objects.filter(adminlevel__id=level)
        annotated = locations.annotate(
            adminarea_id=Subquery(
                areas.filter(geom__intersects=OuterRef('geom')).annotate(
                    adminarea_id=Min('id')
                    ).values('adminarea_id')[:1],
                output_field=IntegerField()
            )
        )
        return annotated
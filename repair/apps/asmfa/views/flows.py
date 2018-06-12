# API View
from abc import ABC

from rest_framework.viewsets import ModelViewSet
from reversion.views import RevisionMixin
from rest_framework.response import Response
from django.http import HttpResponseBadRequest
from django.db.models import Q, Subquery, Min, IntegerField, OuterRef, Sum
import time
import numpy as np
import copy
import json
from collections import defaultdict, OrderedDict
from django.utils.translation import ugettext_lazy as _

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

from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet,
                                     PostGetViewMixin)


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


class Actor2ActorViewSet(PostGetViewMixin, FlowViewSet):
    add_perm = 'asmfa.add_actor2actor'
    change_perm = 'asmfa.change_actor2actor'
    delete_perm = 'asmfa.delete_actor2actor'
    queryset = Actor2Actor.objects.all()
    serializer_class = Actor2ActorSerializer
    additional_filters = {'origin__included': True,
                          'destination__included': True}
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
    def post_get(self, request, **kwargs):
        '''
        body params:
        body = {
            waste: true / false,  # products or waste, don't pass for both
            
            # filter by origin/destination actors
            subset: {
                direction: "to" / "from" / "both", # return flows to or from filtered actors
                # filter actors by their ids OR by group/activity ids (you may do
                # all the same time, but makes not much sense though)
                activitygroups: [...], # ids of activitygroups
                activities: [...], # ids of activities
                ids = [...] # ids of the actors
                
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
            spatial_level: {  
                activity: {
                    id: id,  # id of activitygroup/activity
                    level: id,  # id of spatial level (as in AdminLevels)
                },
            }
            
            # exclusive to spatial_level
            aggregation_level: 'activity' or 'activitygroup', defaults to actor level
        }
        '''
        self.check_permission(request, 'view')
        SerializerClass = self.get_serializer_class()
        params = {}
        # values of body keys are not parsed
        for key, value in request.data.items():
            try:
                params[key] = json.loads(value)
            except json.decoder.JSONDecodeError:
                params[key] = value
        queryset = self.get_queryset()

        waste_filter = params.get('waste', None)
        subset_filter = params.get('subset', None)
        material_filter = params.get('material', None)
        spatial_aggregation = params.get('spatial_level', None)
        level_aggregation = params.get('aggregation_level', None)
        
        if spatial_aggregation and level_aggregation:
            return HttpResponseBadRequest(_(
                "Aggregation on spatial levels and based on the activity level "
                "can't be performed at the same time" ))

        # filter products (waste=False) or waste (waste=True)
        if waste_filter is not None:
            queryset = queryset.filter(waste=waste_filter)

        # build subset of origins/destinations and direction
        if subset_filter:
            group_ids = subset_filter.get('activitygroups', None)
            activity_ids = subset_filter.get('activities', None)
            actor_ids = subset_filter.get('actors', None)
            direction = subset_filter.get('direction', 'both')
            
            actors = Actor.objects.all()
            if group_ids:
                actors = actors.filter(activity__activitygroup__id__in=group_ids)
            if activity_ids:
                actors = actors.filter(activity__id__in=activity_ids)
            if actor_ids:
                actors = actors.filter(id__in=actor_ids)

            if direction == 'from':
                queryset = queryset.filter(origin__in=actors)
            elif direction == 'to':
                queryset = queryset.filter(destination__in=actors)
            else:
                queryset = queryset.filter(Q(origin__in=actors) |
                                           Q(destination__in=actors))

        aggregate_materials = (False if material_filter is None
                               else material_filter.get('aggregate', False))
        material_id = (None if material_filter is None
                       else material_filter.get('id', None))

        material = None
        # filter the flows by their fractions excluding flows whose
        # fractions don't contain the requested material (incl. child materials)
        if material_id is not None:
            try:
                material = Material.objects.get(id=material_filter['id'])
            except Material.DoesNotExist:
                return Response(status=404)
            queryset = filter_by_material(material, queryset)

        serializer = SerializerClass(queryset, many=True,
                                         context={'request': request, })
        data = serializer.data
    
        # POSTPROCESSING: all following operations are performed on serialized
        # data
        
        if level_aggregation and level_aggregation != 'actors':
            data = self.aggregate_to_level(level_aggregation, data, queryset)

        if spatial_aggregation:
            levels = {}
            types = []
            for node_type, values in spatial_aggregation.items():
                node_id = values['id']
                level_id = values['level']
                levels[node_id] = level_id
                types.append(node_type)
            unique_types = np.unique(types)
            # ToDo: raise HTTP malformed request 
            if len(unique_types) != 1:
                return HttpResponseBadRequest(_(
                    'Only one type of activity level is allowed at the same '
                    'type when aggregating on spatial levels'))
            typ = unique_types[0]
            if typ == 'activity':
                group_relation = 'activity'
            elif typ == 'activitygroup':
                group_relation = 'activity__activitygroup'
            else:
                return HttpResponseBadRequest(_('unknown activity level'))
            data = self.spatial_aggregation(data, queryset,
                                            group_relation, levels)

        # if the fractions of flows are filtered by material, the other
        # fractions should be removed from the returned data        
        if material and not aggregate_materials:
            # if the fractions of flows are filtered by material, the other
            # fractions should be removed from the returned data
            if not aggregate_materials:
                process_data_fractions(material, material.children,
                                       data, aggregate_materials=False)
                return Response(data)

        # aggregate the fractions of the queryset
        if aggregate_materials:
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
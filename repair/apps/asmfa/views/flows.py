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
from django.contrib.gis.db.models import Union

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
    Actor2ActorCreateSerializer
)

from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet,
                                     PostGetViewMixin)


class ReasonViewSet(RevisionMixin, ModelViewSet):
    pagination_class = None
    serializer_class = ReasonSerializer
    queryset = Reason.objects.all()

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

def get_descendants(mat_id, mat_dict):
    descendants = []
    children = mat_dict.get(mat_id, [])
    for child_id in children:
        descendants.append(child_id)
        descendants.extend(get_descendants(child_id, mat_dict))
    return descendants

def filter_by_material(materials, queryset):
    """filter queryset by their compositions,
    their fractions have to contain the given material or children
    of the material"""
    mats = []
    all_materials = Material.objects.values_list('id', 'parent__id')
    mat_dict = {}
    for mat_id, parent_id in all_materials:
        if not parent_id:
            continue
        parent_entry = mat_dict.get(parent_id)
        if not parent_entry:
            parent_entry = []
            mat_dict[parent_id] = parent_entry
        parent_entry.append(mat_id)

    for material in materials:
        # get the children of the given material
        mats.extend(get_descendants(material.id, mat_dict))
        #mats.extend(material.descendants)
        # fractions have to contain children and the material itself
        mats.append(material.id)
    fractions = ProductFraction.objects.filter(material__id__in=mats)
    # the compositions containing the filtered fractions
    compositions = fractions.values('composition')
    # the flows containing the filtered compositions
    filtered = queryset.filter(composition__in=compositions)
    return filtered

def aggregate_fractions(materials, data, unaltered_materials=[],
                        aggregate_materials=False):
    '''
    aggregate the fractions to given materials, all fractions with child
    materials of given materials will be summed up to the level of those,
    amount will be recalculated

    if aggregate_materials is False the materials won't be aggregated, but
    all materials that are not children of given materials will be removed
    from flow and amount will still be recalculated

    unaltered materials will be kept as is and ignored when
    aggregating children (may be parents as well)
    '''
    if not materials and not aggregate_materials:
        return data
    materials = materials or []
    unaltered_dict = dict([(mat.id, mat) for mat in unaltered_materials])
    # dictionary to store requested materials and if other materials are
    # descendants of those (including the material itself), much faster than
    # repeatedly getting the materials and their ancestors
    desc_dict = dict([(mat, { mat.id: True }) for mat in materials])
    new_data = []
    for serialized_flow in data:
        # aggregation is requested on no given materials ->
        # aggregate to top level (just meaning: keep amount, remove fractions)
        if not materials and aggregate_materials:
            serialized_flow['composition'] = None
        else:
            composition = serialized_flow['composition']
            if not composition:
                continue
            old_total = serialized_flow['amount']
            new_total = 0
            aggregated_amounts = defaultdict.fromkeys(materials, 0)
            for mat in unaltered_materials:
                aggregated_amounts[mat] = 0
            # remove fractions that are no descendants of the material
            valid_fractions = []
            for serialized_fraction in composition['fractions']:
                fraction_mat_id = serialized_fraction['material']
                # keep the fraction as is
                if fraction_mat_id in unaltered_dict:
                    aggregated_amounts[unaltered_dict[fraction_mat_id]] += (
                        serialized_fraction['fraction'] * old_total)
                    valid_fractions.append(serialized_fraction)
                    continue
                for mat in materials:
                    child_dict = desc_dict[mat]
                    is_desc = child_dict.get(fraction_mat_id)
                    # save time by doing this once and storing it
                    if is_desc is None:
                        fraction_material = Material.objects.get(
                            id=fraction_mat_id)
                        child_dict[fraction_mat_id] = is_desc = \
                            fraction_material.is_descendant(mat)
                    if is_desc:
                        amount = serialized_fraction['fraction'] * old_total
                        aggregated_amounts[mat] += amount
                        new_total += amount
                        valid_fractions.append(serialized_fraction)
            # amount zero -> there is actually no flow
            if new_total == 0:
                continue
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
                    fraction['fraction'] = fraction['fraction'] * old_total / new_total
                    new_fractions.append(fraction)

            serialized_flow['amount'] = new_total
            composition['fractions'] = new_fractions

        new_data.append(serialized_flow)
    return new_data

def aggregate_to_level(data, queryset, origin_level, destination_level, is_stock=False):
    """
    Aggregate actor level to the according flow/stock level
    if not implemented in the subclass, do nothing
    almost the same for flows and stocks except missing destinations for stocks
    """
    if not origin_level and not destination_level:
        return data
    origin_level = origin_level or 'actor'
    destination_level = destination_level or 'actor'

    origins = Actor.objects.filter(id__in=queryset.values_list('origin'));
    if origin_level.lower() == 'activity':
        origins_map = dict(origins.values_list('id', 'activity'))
        args = ['origin__activity']
    elif origin_level.lower() == 'activitygroup':
        origins_map = dict(Actor.objects.values_list(
                'id', 'activity__activitygroup'))
        args = ['origin__activity__activitygroup']
    else:
        origins_map = dict(origins.values_list('id', 'id'))
        args = ['origin__id']

    if not is_stock:
        destinations = Actor.objects.filter(id__in=queryset.values_list('destination'));

        if destination_level.lower() == 'activity':
            destinations_map = dict(destinations.values_list(
                'id', 'activity'))
            args.append('destination__activity')
        elif destination_level.lower() == 'activitygroup':
            destinations_map = dict(destinations.values_list(
                'id', 'activity__activitygroup'))
            args.append('destination__activity__activitygroup')
        else:
            destinations_map = dict(destinations.values_list('id', 'id'))
            args.append('destination__id')

    acts = queryset.values_list(*args)

    act2act_amounts = acts.annotate(Sum('amount'))
    custom_compositions = dict()
    total_amounts = dict()
    new_flows = list()
    for values in act2act_amounts:
        if is_stock:
            origin, amount = values
            destination = None
        else:
            origin, destination, amount = values
        key = (origin, destination)
        total_amounts[key] = amount
        custom_composition = copy.deepcopy(composition_struct)
        custom_composition['masses_of_materials'] = OrderedDict()
        custom_compositions[key] = custom_composition

    for serialized_flow in data:
        amount = serialized_flow['amount']
        composition = serialized_flow['composition']
        if not composition:
            continue
        origin = origins_map[serialized_flow['origin']]
        destination = None if is_stock else \
            destinations_map[serialized_flow['destination']]
        key = (origin, destination)
        custom_composition = custom_compositions[key]
        masses_of_materials = custom_composition['masses_of_materials']

        fractions = composition['fractions']
        for fraction in fractions:
            mass = amount * fraction['fraction']
            material = fraction['material']
            mass_of_material = masses_of_materials.get(material, 0) + mass
            masses_of_materials[material] = mass_of_material

    for values in act2act_amounts:
        if is_stock:
            origin, amount = values
            destination = None
        else:
            origin, destination, amount = values
        key = (origin, destination)
        custom_composition = custom_compositions[key]
        masses_of_materials = custom_composition['masses_of_materials']
        fractions = list()
        for material, mass_of_material in masses_of_materials.items():
            fraction = mass_of_material / amount if amount != 0 else 0
            new_fraction = copy.deepcopy(fractions_struct)
            new_fraction['material'] = material
            new_fraction['fraction'] = fraction
            fractions.append(new_fraction)
        custom_composition['fractions'] = fractions
        del(custom_composition['masses_of_materials'])

        new_flow = copy.deepcopy(flow_struct)
        new_flow['amount'] = amount
        new_flow['origin'] = origin
        new_flow['origin_level'] = origin_level
        new_flow['composition'] = custom_composition
        new_flow['id'] = 'agg-{}'.format(origin)

        if not is_stock:
            new_flow['destination'] = destination
            new_flow['destination_level'] = destination_level
            new_flow['id'] += '-{}'.format(destination)
        else:
            del new_flow['destination']
            del new_flow['destination_level']
        new_flows.append(new_flow)
    return new_flows

def build_area_filter(function_name, values, keyflow_id):
    actors = Actor.objects.filter(
        activity__activitygroup__keyflow__id = keyflow_id)
    areas = Area.objects.filter(id__in = values).aggregate(area=Union('geom'))
    actors = actors.filter(
        administrative_location__geom__intersects=areas['area'])
    rest_func = 'origin__id__in' if function_name == 'origin__areas' \
        else 'destination__id__in'
    return rest_func, actors.values_list('id')


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
    serializers = {
        'list': Actor2ActorSerializer,
        'create': Actor2ActorCreateSerializer,
    }
    additional_filters = {'origin__included': True,
                          'destination__included': True}
    # POST is used to send filter parameters not to create
    def post_get(self, request, **kwargs):
        '''
        body params:
        body = {
            waste: true / false,  # products or waste, don't pass for both

            # prefilter flows
            # list of subfilters, subfilters are 'and' linked
            filters: [
                {
                    link : 'and' or 'or' (default 'or')
                    functions: [
                        {
                             function: django filter function (e.g. origin__id__in)
                             values: values for filter function (e.g. [1,5,10])
                        },
                        ...
                    ]
                },
                ...
            ],

            filter_link: and/or, # logical linking of filters, defaults to 'or'

            # filter/aggregate by given material
            materials: {
                ids: [...], # ids of materials to filter, only flows with those materials and their children will be returned, other materials will be ignored
                unaltered: [...], # ids of materials that should be kept as they are when aggregating
                aggregate: true / false, # if true the children of the given materials will be aggregated, aggregates to top level materials if no ids were given
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
            aggregation_level: {
                origin: 'activity' or 'activitygroup', defaults to actor level
                destination: 'activity' or 'activitygroup', defaults to actor level
            }
        }
        '''
        SerializerClass = self.get_serializer_class()
        self.check_permission(request, 'view')
        # filter by query params
        queryset = self._filter(kwargs, query_params=request.query_params,
                                SerializerClass=self.get_serializer_class())
        params = {}
        # values of body keys are not parsed
        for key, value in request.data.items():
            try:
                params[key] = json.loads(value)
            except json.decoder.JSONDecodeError:
                params[key] = value

        waste_filter = params.get('waste', None)
        filters = params.get('filters', None)
        material_filter = params.get('materials', None)
        spatial_aggregation = params.get('spatial_level', None)
        level_aggregation = params.get('aggregation_level', None)

        if spatial_aggregation and level_aggregation:
            return HttpResponseBadRequest(_(
                "Aggregation on spatial levels and based on the activity level "
                "can't be performed at the same time" ))

        # filter products (waste=False) or waste (waste=True)
        if waste_filter is not None:
            queryset = queryset.filter(waste=waste_filter)
        keyflow = kwargs['keyflow_pk']
        # filter queryset based on passed filters
        if filters:
            for sub_filter in filters:
                filter_link = sub_filter.get('link', None)
                filter_functions = []
                for f in sub_filter['functions']:
                    func = f['function']
                    v = f['values']
                    if func.endswith('__areas'):
                        func, v = build_area_filter(func, v, keyflow)
                    filter_function = Q(**{func: v})
                    filter_functions.append(filter_function)
                if filter_link == 'and':
                    link_func = np.bitwise_and
                else:
                    link_func = np.bitwise_or
                if len(filter_functions) == 1:
                    queryset = queryset.filter(filter_functions[0])
                if len(filter_functions) > 1:
                    queryset = queryset.filter(link_func.reduce(filter_functions))

        keyflow = kwargs['keyflow_pk']
        actors = Actor.objects.filter(
            activity__activitygroup__keyflow__id=keyflow)

        aggregate_materials = (False if material_filter is None
                               else material_filter.get('aggregate', False))
        material_ids = (None if material_filter is None
                        else material_filter.get('ids', None))
        unaltered_material_ids = ([] if material_filter is None
                                  else material_filter.get('unaltered', []))

        materials = None
        unaltered_materials = []
        # filter the flows by their fractions excluding flows whose
        # fractions don't contain the requested material (incl. child materials)
        if material_ids is not None:
            materials = Material.objects.filter(id__in=material_ids)
            unaltered_materials = Material.objects.filter(
                id__in=unaltered_material_ids)
            queryset = filter_by_material(
                list(materials) + list(unaltered_materials), queryset)

        serializer = SerializerClass(queryset, many=True,
                                     context={'request': request, })
        data = serializer.data

        # POSTPROCESSING: all following operations are performed on serialized
        # data

        if level_aggregation:
            origin_level = level_aggregation['origin']
            destination_level = level_aggregation['destination']
            data = aggregate_to_level(
                data, queryset, origin_level, destination_level)

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

        # materials were given and/or materials shall be aggregated
        if materials or aggregate_materials:
            data = aggregate_fractions(
                materials, data, aggregate_materials=aggregate_materials,
                unaltered_materials=unaltered_materials
            )
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
            all().\
            defer('keyflow__note').\
            defer('keyflow__casestudy__geom').\
            defer('keyflow__casestudy__focusarea')

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
            new_flow = copy.deepcopy(flow_struct)
            new_flows.append(new_flow)
            amount = aggregation['amount']
            new_flow['amount'] = aggregation['amount']
            new_comp = copy.deepcopy(composition_struct)
            new_flow['composition'] = new_comp
            new_flow['origin'] = origin
            new_flow['destination'] = destination
            origin_level = area_levels.get(origin, None)
            destination_level = area_levels.get(destination, None)
            new_flow['origin_level'] = origin_level
            new_flow['destination_level'] = destination_level
            for material, mass in aggregation['fractions'].items():
                new_fract = copy.deepcopy(fractions_struct)
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

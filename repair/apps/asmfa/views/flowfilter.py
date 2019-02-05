from collections import defaultdict, OrderedDict
from rest_framework.viewsets import ModelViewSet
from reversion.views import RevisionMixin
from rest_framework.response import Response
from django.http import HttpResponseBadRequest
from django.db.models import Q, Subquery, Min, IntegerField, OuterRef, Sum, F
import time
import numpy as np
import copy
import json
from collections import defaultdict, OrderedDict
from django.utils.translation import ugettext_lazy as _
from django.contrib.gis.db.models import Union

from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet,
                                     PostGetViewMixin)


from repair.apps.asmfa.models import (
    Flow,
    AdministrativeLocation,
    Actor2Actor,
    Group2Group,
    Material,
    FractionFlow,
    Actor,
    ActivityGroup,
    Activity,
    AdministrativeLocation
)

from repair.apps.asmfa.serializers import (
    FractionFlowSerializer
)

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

FILTER_SUFFIX = {
    Actor: '',
    Activity: '__activity',
    ActivityGroup: '__activity__activitygroup'
}

LEVEL_KEYWORD = {
    Actor: 'actor',
    Activity: 'activity',
    ActivityGroup: 'activitygroup'
}

def descend_materials(materials, queryset):
    """return list of material ids of given materials and all of their
    descendants
    """
    mats = []
    all_materials = Material.objects.values_list('id', 'parent__id')
    mat_dict = {}

    # might seems strange to build a dict with all materials and it's
    # children, but this is in fact 1000 times faster than
    # doing this in iteration over given material queryset
    for mat_id, parent_id in all_materials:
        if not parent_id:
            continue
        parent_entry = mat_dict.get(parent_id)
        if not parent_entry:
            parent_entry = []
            mat_dict[parent_id] = parent_entry
        parent_entry.append(mat_id)

    def get_descendants(mat_id):
        descendants = []
        children = mat_dict.get(mat_id, [])
        for child_id in children:
            descendants.append(child_id)
            descendants.extend(get_descendants(child_id))
        return descendants

    # use the dict to get all descending child materials
    for material in materials:
        # get the children of the given material
        mats.extend(get_descendants(material.id))
        # fractions have to contain children and the material itself
        mats.append(material.id)
    return mats


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


class FilterFlowViewSet(PostGetViewMixin, RevisionMixin,
                        CasestudyViewSetMixin,
                        ModelPermissionViewSet):
    serializer_class = FractionFlowSerializer
    model = FractionFlow

    queryset = FractionFlow.objects.all()
    #additional_filters = {'origin__included': True,
                          #'destination__included': True}

    def get_queryset(self):
        keyflow_pk = self.kwargs.get('keyflow_pk')
        flows = FractionFlow.objects.filter(keyflow__id=keyflow_pk)
        return flows.order_by('origin', 'destination')

    # POST is used to send filter parameters not to create
    def post_get(self, request, **kwargs):
        '''
        body params:
        body = {
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
        self.check_permission(request, 'view')
        # filter by query params
        queryset = self._filter(kwargs, query_params=request.query_params,
                                SerializerClass=self.get_serializer_class())

        # filter flows between included actors (resp. origin only if stock)
        queryset = queryset.filter(
            Q(origin__included=True) &
            (Q(destination__included=True) | Q(destination__isnull=True))
        )
        params = {}
        # values of body keys are not parsed
        for key, value in request.data.items():
            try:
                params[key] = json.loads(value)
            except json.decoder.JSONDecodeError:
                params[key] = value

        filter_chains = params.get('filters', None)
        material_filter = params.get('materials', None)
        spatial_aggregation = params.get('spatial_level', None)

        l_a = params.get('aggregation_level', {})
        inv_map = {v: k for k, v in LEVEL_KEYWORD.items()}
        origin_level = inv_map[l_a['origin']] if 'origin' in l_a else Actor
        destination_level = inv_map[l_a['destination']] \
            if 'destination' in l_a else Actor

        if spatial_aggregation and level_aggregation:
            return HttpResponseBadRequest(_(
                "Aggregation on spatial levels and based on the activity level "
                "can't be performed at the same time" ))

        keyflow = kwargs['keyflow_pk']
        # filter queryset based on passed filters
        if filter_chains:
            queryset = self.filter_chain(queryset, filter_chains)

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
        #if material_ids is not None:
            #materials = Material.objects.filter(id__in=material_ids)
            #unaltered_materials = Material.objects.filter(
                #id__in=unaltered_material_ids)
            #queryset = filter_by_materials(
                #queryset, list(materials) + list(unaltered_materials))

        data = self.serialize(queryset, origin_model=origin_level,
                              destination_model=destination_level)
        return Response(data)

    def list(self, request, **kwargs):
        self.check_permission(request, 'view')
        self.check_casestudy(kwargs, request)

        queryset = self._filter(kwargs, query_params=request.query_params)
        if queryset is None:
            return Response(status=400)
        data = self.serialize(queryset)
        return Response(data)

    @staticmethod
    def serialize_nodes(nodes, add_locations=False):
        '''
        serialize actors, activities or groups in the same way
        add_locations works only for actors
        '''
        args = ['id', 'name']
        if add_locations:
            args.append('administrative_location__geom')
        node_dict = dict(
            zip(nodes.values_list('id', flat=True),
                nodes.values(*args))
        )
        if add_locations:
            for k, v in node_dict.items():
                geom = v.pop('administrative_location__geom')
                v['geom'] = json.loads(geom.geojson) if geom else None
        node_dict[None] = None
        return node_dict

    def serialize(self, queryset, origin_model=Actor, destination_model=Actor):
        origin_filter = 'origin' + FILTER_SUFFIX[origin_model]
        destination_filter = 'destination' + FILTER_SUFFIX[destination_model]
        origin_level = LEVEL_KEYWORD[origin_model]
        destination_level = LEVEL_KEYWORD[destination_model]
        data = []
        start = time.time()
        flow_ids = queryset.values('id')
        origins = origin_model.objects.filter(
            id__in=queryset.values(origin_filter))
        destinations = destination_model.objects.filter(
            id__in=queryset.values(destination_filter))
        # reset order to avoid Django ORM bug with determining
        # distinct values in ordered querysets
        queryset = queryset.order_by()

        groups = queryset.values(origin_filter, destination_filter,
                                 'waste', 'to_stock').distinct()

        origin_dict = self.serialize_nodes(
            origins, add_locations=True if origin_model == Actor else False
        )
        destination_dict = self.serialize_nodes(
            destinations,
            add_locations=True if destination_model == Actor else False
        )

        for group in groups:
            grouped = queryset.filter(**group)
            # sum over all rows in group
            amount = list(grouped.aggregate(Sum('amount')).values())[0]
            origin_item = origin_dict[group[origin_filter]]
            origin_item['level'] = origin_level
            dest_item = destination_dict[group[destination_filter]]
            if dest_item:
                dest_item['level'] = destination_level
            # sum up same materials
            grouped_mats = grouped.values('material').annotate(
                name=F('material__name'),
                level=F('material__level'),
                amount=Sum('amount')
            )
            flow_item = OrderedDict((
                ('origin', origin_item),
                ('destination', dest_item),
                ('waste', group['waste']),
                ('stock', group['to_stock']),
                ('amount', amount),
                ('materials', grouped_mats)
            ))

            data.append(flow_item)
        print(time.time() - start)
        return data

    @staticmethod
    def filter_chain(queryset, filters):
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
        return queryset

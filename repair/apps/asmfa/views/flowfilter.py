from collections import defaultdict, OrderedDict
from rest_framework.viewsets import ModelViewSet
from reversion.views import RevisionMixin
from django.contrib.gis.geos import GEOSGeometry
from django.http import HttpResponseBadRequest, HttpResponse
import numpy as np
import copy
import json
from collections import defaultdict, OrderedDict
from django.utils.translation import ugettext_lazy as _
from django.contrib.gis.db.models import Union
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import (Q, Sum, F, QuerySet)

from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet,
                                     PostGetViewMixin)
from repair.apps.utils.utils import (descend_materials,
                                     get_annotated_fractionflows)

from repair.apps.asmfa.models import (
    Flow, AdministrativeLocation, Actor2Actor, Group2Group,
    Material, FractionFlow, Actor, ActivityGroup, Activity,
    AdministrativeLocation, Process, StrategyFractionFlow
)
from repair.apps.changes.models import Strategy
from repair.apps.studyarea.models import Area

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

    @action(methods=['get', 'post'], detail=False)
    def count(self, request, **kwargs):
        query_params = request.query_params.copy()
        material = query_params.pop('material', None)
        include_children = query_params.pop('include_child_materials', None)
        queryset = self._filter(kwargs, query_params=query_params)

        if (material is not None):
            mat_id = material[0]
            if include_children:
                mats = Material.objects.filter(
                    id__in=descend_materials([Material.objects.get(id=mat_id)]))
                queryset = queryset.filter(strategy_material__in=mats)
            else:
                queryset = queryset.filter(strategy_material=mat_id)

        if ('origin_area' in request.data):
            geojson = self.request.data['origin_area']
            poly = GEOSGeometry(geojson)
            queryset = queryset.filter(
                origin__administrative_location__geom__intersects=poly)
        if ('destination_area' in request.data):
            geojson = self.request.data['destination_area']
            poly = GEOSGeometry(geojson)
            queryset = queryset.filter(
                destination__administrative_location__geom__intersects=poly)
        json = {'count': queryset.count()}
        return Response(json)

    def get_queryset(self):
        keyflow_pk = self.kwargs.get('keyflow_pk')
        strategy = self.request.query_params.get('strategy', None)
        return get_annotated_fractionflows(keyflow_pk, strategy_id=strategy)

    # POST is used to send filter parameters not to create
    def post_get(self, request, **kwargs):
        '''
        body params:
        body = {
            # prefilter flows
            # list of subfilters, subfilters are 'and' linked
            # keys: django filter function (e.g. origin__id__in)
            # values: values for filter function (e.g. [1,5,10])
            filters: [
                {
                    link : 'and' or 'or' (default 'and'),
                    some-django-filter-function: value,
                    another-django-filter-function: value
                },
                { link: ... },
                ....
            ],

            # filter/aggregate by given material
            materials: {
                ids: [...], # ids of materials to filter, only flows with those materials and their children will be returned, other materials will be ignored
                unaltered: [...], # ids of materials that should be kept as they are when aggregating
                aggregate: true / false, # if true the children of the given materials will be aggregated, aggregates to top level materials if no ids were given
            },

            aggregation_level: {
                origin: 'activity' or 'activitygroup', defaults to actor level
                destination: 'activity' or 'activitygroup', defaults to actor level
            }
        }
        '''
        self.check_permission(request, 'view')

        strategy_id = request.query_params.get('strategy', None)
        if strategy_id is not None:
            strategy = Strategy.objects.get(id=strategy_id)
            if strategy.status == 0:
                return HttpResponseBadRequest(
                    _('calculation is not done yet'))
            if strategy.status == 1:
                return HttpResponseBadRequest(
                    _('calculation is still in process'))

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

        l_a = params.get('aggregation_level', {})
        inv_map = {v: k for k, v in LEVEL_KEYWORD.items()}
        origin_level = inv_map[l_a['origin']] if 'origin' in l_a else Actor
        destination_level = inv_map[l_a['destination']] \
            if 'destination' in l_a else Actor

        keyflow = kwargs['keyflow_pk']
        # filter queryset based on passed filters
        if filter_chains:
            queryset = self.filter_chain(queryset, filter_chains, keyflow)

        aggregate_materials = (False if material_filter is None
                               else material_filter.get('aggregate', False))
        material_ids = (None if material_filter is None
                        else material_filter.get('ids', None))
        unaltered_material_ids = ([] if material_filter is None
                                  else material_filter.get('unaltered', []))
        materials = None
        unaltered_materials = []
        # filter the flows by their fractions excluding flows whose
        # fractions don't contain the requested materials
        # (including child materials)
        if material_ids is not None:
            materials = Material.objects.filter(id__in=material_ids)
            unaltered_materials = Material.objects.filter(
                id__in=unaltered_material_ids)

            mats = descend_materials(list(materials) +
                                     list(unaltered_materials))
            queryset = queryset.filter(
                strategy_material__in=Material.objects.filter(id__in=mats))

        agg_map = None
        try:
            if aggregate_materials:
                agg_map = self.map_aggregation(
                    queryset, materials,
                    unaltered_materials=unaltered_materials)
        except RecursionError as e:
            return HttpResponse(content=str(e), status=500)

        data = self.serialize(queryset, origin_model=origin_level,
                              destination_model=destination_level,
                              aggregation_map=agg_map)
        return Response(data)

    def _filter(self, lookup_args, query_params=None, SerializerClass=None):
        if query_params:
            query_params = query_params.copy()
            strategy = query_params.pop('strategy', None)
            for key in query_params:
                if (key.startswith('material') or
                    key.startswith('waste') or
                    key.startswith('hazardous') or
                    key.startswith('process') or
                    key.startswith('amount')):
                    query_params['strategy_'+key] = query_params.pop(key)[0]
            # rename filter for stock, as this relates to field with stock pk
            # but serializer returns boolean in this field (if it is stock)
            stock_filter = query_params.pop('stock', None)
            if stock_filter is not None:
                query_params['to_stock'] = stock_filter[0]
        queryset = super()._filter(lookup_args, query_params=query_params,
                                   SerializerClass=SerializerClass)
        return queryset

    def list(self, request, **kwargs):
        self.check_permission(request, 'view')
        self.check_casestudy(kwargs, request)

        queryset = self._filter(kwargs, query_params=request.query_params)
        if queryset is None:
            return Response(status=400)
        data = self.serialize(queryset)
        return Response(data)

    @staticmethod
    def map_aggregation(queryset, materials, unaltered_materials=[]):
        ''' return map with material-ids that shall be aggregated as keys and
        the materials they are aggregated to as values

        materials are the materials to aggregate to, unaltered_materials
        contains ids of materials that are ignored while doing this (shall
        be kept)
        '''
        agg_map = {}

        # workaround: reset order to avoid Django ORM bug with determining
        # distinct values in ordered querysets
        queryset = queryset.order_by()
        materials_used = queryset.values('strategy_material').distinct()
        materials_used = Material.objects.filter(id__in=materials_used)
        #  no materials given -> aggregate to top level
        if not materials:
            # every material will be aggregated to the top ancestor
            for material in materials_used:
                if material.id not in unaltered_materials:
                    agg_map[material.id] = material.top_ancestor
                else:
                    agg_map[material.id] = material

        else:
            exclusion = []
            # look for parent material for each material in use
            for mat_used in materials_used:
                found = False
                if mat_used in unaltered_materials:
                    found = True
                    agg_map[mat_used.id] = mat_used
                else:
                    for material in materials:
                        #  found yourself
                        if mat_used == material:
                            found = True
                            agg_map[mat_used.id] = mat_used
                            break
                        #  found parent
                        if mat_used.is_descendant(material):
                            found = True
                            agg_map[mat_used.id] = material
                            break

                if not found:
                    exclusion.append(flow.id)
            # exclude flows not in material hierarchy, shouldn't happen if
            # correctly filtered before, but doesn't hurt
            filtered = queryset.exclude(id__in=exclusion)
        return agg_map

    @staticmethod
    def serialize_nodes(nodes, add_locations=False, add_fields=[]):
        '''
        serialize actors, activities or groups in the same way
        add_locations works, only for actors
        '''
        args = ['id', 'name'] + add_fields
        if add_locations:
            args.append('administrative_location__geom')
        values = nodes.values(*args)
        node_dict = {v['id']: v for v in values}
        if add_locations:
            for k, v in node_dict.items():
                geom = v.pop('administrative_location__geom')
                v['geom'] = json.loads(geom.geojson) if geom else None
        node_dict[None] = None
        return node_dict

    def serialize(self, queryset, origin_model=Actor, destination_model=Actor,
                  aggregation_map=None):
        '''
        serialize given queryset of fraction flows to JSON,
        aggregates flows between nodes on actor level to the levels determined
        by origin_model and destination_model,

        aggregation_map contains ids of materials as keys that should be
        aggregated to certain materials (values)
        (e.g. to aggregate child materials to their parents)
        '''
        strategy = self.request.query_params.get('strategy', None)
        origin_filter = 'origin' + FILTER_SUFFIX[origin_model]
        destination_filter = 'destination' + FILTER_SUFFIX[destination_model]
        origin_level = LEVEL_KEYWORD[origin_model]
        destination_level = LEVEL_KEYWORD[destination_model]
        data = []
        origins = origin_model.objects.filter(
            id__in=list(queryset.values_list(origin_filter, flat=True)))
        destinations = destination_model.objects.filter(
            id__in=list(queryset.values_list(destination_filter, flat=True)))
        # workaround Django ORM bug
        queryset = queryset.order_by()

        groups = queryset.values(
            origin_filter, destination_filter,
            'strategy_waste', 'strategy_process', 'to_stock',
            'strategy_hazardous').distinct()

        def get_code_field(model):
            if model == Actor:
                return 'activity__nace'
            if model == Activity:
                return 'nace'
            return 'code'

        origin_dict = self.serialize_nodes(
            origins, add_locations=True if origin_model == Actor else False,
            add_fields=[get_code_field(origin_model)]
        )
        destination_dict = self.serialize_nodes(
            destinations,
            add_locations=True if destination_model == Actor else False,
            add_fields=[get_code_field(destination_model)]
        )

        for group in groups:
            grouped = queryset.filter(**group)
            origin_item = origin_dict[group[origin_filter]]
            origin_item['level'] = origin_level
            dest_item = destination_dict[group[destination_filter]]
            if dest_item:
                dest_item['level'] = destination_level
            # sum up same materials
            annotation = {
                'material': F('strategy_material'),
                'name':  F('strategy_material_name'),
                'level': F('strategy_material_level'),
                #'delta': Sum('strategy_delta'),
                'amount': Sum('strategy_amount')
            }
            grouped_mats = \
                list(grouped.values('strategy_material').annotate(**annotation))
            # aggregate materials according to mapping aggregation_map
            if aggregation_map:
                aggregated = {}
                for grouped_mat in grouped_mats:
                    mat_id = grouped_mat['strategy_material']
                    amount = grouped_mat['amount']
                    mapped = aggregation_map[mat_id]

                    agg_mat_ser = aggregated.get(mapped.id, None)
                    # create dict for aggregated materials if there is none
                    if not agg_mat_ser:
                        agg_mat_ser = {
                            'material': mapped.id,
                            'name': mapped.name,
                            'level': mapped.level,
                            'amount': amount,
                            #'delta': grouped_mat['delta']
                        }
                        aggregated[mapped.id] = agg_mat_ser
                    # just sum amounts up if dict is already there
                    else:
                        agg_mat_ser['amount'] += amount
                        #if strategy is not None:
                            #agg_mat_ser['delta'] += grouped_mat['delta']
                grouped_mats = aggregated.values()
            process = Process.objects.get(id=group['strategy_process']) \
                if group['strategy_process'] else None
            # sum over all rows in group
            #sq_total_amount = list(grouped.aggregate(Sum('amount')).values())[0]
            strat_total_amount = list(
                grouped.aggregate(Sum('strategy_amount')).values())[0]
            #deltas = list(grouped.aggregate(Sum('strategy_delta')).values())[0]
            flow_item = OrderedDict((
                ('origin', origin_item),
                ('destination', dest_item),
                ('waste', group['strategy_waste']),
                ('hazardous', group['strategy_hazardous']),
                ('stock', group['to_stock']),
                ('process', process.name if process else ''),
                ('process_id', process.id if process else None),
                ('amount', strat_total_amount),
                ('materials', grouped_mats),
                #('delta', deltas)
            ))
            data.append(flow_item)
        return data

    @staticmethod
    def filter_chain(queryset, filters, keyflow):
        for sub_filter in filters:
            filter_link = sub_filter.pop('link', 'and')
            filter_functions = []
            for func, v in sub_filter.items():
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


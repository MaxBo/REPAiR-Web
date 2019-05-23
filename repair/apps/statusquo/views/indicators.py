from reversion.views import RevisionMixin
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnList
from rest_framework.decorators import action
from django.http import Http404
from abc import ABCMeta
from enum import Enum
import numpy as np
from django.db.models import Q, Sum, Case, When, F, Value
from collections import OrderedDict
from django.utils.translation import ugettext as _
from django.contrib.gis.geos import GEOSGeometry
from django.db.models.functions import Coalesce

from repair.apps.asmfa.views import descend_materials
from repair.apps.utils.views import (ModelPermissionViewSet,
                                     CasestudyViewSetMixin)
from repair.apps.asmfa.models import Actor, FractionFlow, AdministrativeLocation
from repair.apps.asmfa.serializers import Actor2ActorSerializer
from repair.apps.changes.models import Strategy
from repair.apps.statusquo.models import FlowIndicator, IndicatorType
from repair.apps.statusquo.serializers import FlowIndicatorSerializer
from repair.apps.studyarea.models import Area


def filter_actors_by_area(actors, geom):
    '''
    get actors in a polygon (by administrative location)
    '''
    locations = AdministrativeLocation.objects.filter(actor__in=actors)
    locations = locations.filter(geom__intersects=geom)
    actors_in_area = actors.filter(id__in=locations.values('actor'))
    return actors_in_area


class ComputeIndicator(metaclass=ABCMeta):
    '''
    abstract class for computing indicators
    '''
    description = ''
    name = ''
    default_unit = ''

    def __init__(self, strategy=None):
        self.strategy = strategy

    def get_queryset(self, indicator_flow, geom=None):
        '''filter all flows by IndicatorFlow attributes,
        optionally filter for geometry'''
        # there might be unset indicators -> return empty queryset
        # (calculation will return zero)
        if not indicator_flow:
            return FractionFlow.objects.none()
        materials = indicator_flow.materials.all()

        flow_type = indicator_flow.flow_type.name
        hazardous = indicator_flow.hazardous.name
        avoidable = indicator_flow.avoidable.name

        # filter flows by type (waste/product/both)
        flows = FractionFlow.objects.all()

        if self.strategy:
            # ToDo: material
            flows = flows.filter(
                (
                    Q(f_strategyfractionflow__isnull = True) |
                    Q(f_strategyfractionflow__strategy = self.strategy)
                )
            ).annotate(
                # strategy fraction flow overrides amounts
                strategy_amount=Coalesce(
                    'f_strategyfractionflow__amount', 'amount'),
                # set new flow amounts to zero for status quo
                statusquo_amount=Case(
                    When(strategy__isnull=True, then=F('amount')),
                    default=Value(0),
                )
            )
        else:
            # flows without filters for status quo
            flows = flows.filter(strategy__isnull=True)
            # just for convenience, use field statusquo_amount
            flows = flows.annotate(statusquo_amount=F('amount'))
        if flow_type != 'BOTH':
            is_waste = True if flow_type == 'WASTE' else False
            flows = flows.filter(waste=is_waste)
        if hazardous != 'BOTH':
            is_hazardous = True if hazardous == 'YES' else False
            flows = flows.filter(hazardous=is_hazardous)
        if avoidable != 'BOTH':
            is_avoidable = True if avoidable == 'YES' else False
            flows = flows.filter(avoidable=is_avoidable)

        # filter flows by processes
        process_ids = indicator_flow.process_ids
        if (process_ids):
            process_ids = process_ids.split(',')
            flows = flows.filter(process__id__in=process_ids)

        if materials:
            mats = descend_materials(list(materials))
            flows = flows.filter(material__id__in=mats)

        # ToDo: implement new filter attribute sinks and sources only
        #destinations_to_exclude = flows.exclude(destination__isnull=True).values('destination__id').distinct()
        ##flows_to_exclude = flows.filter(origin__in=destinations_to_exclude)
        #flows2 = flows.exclude(origin__id__in=destinations_to_exclude)

        # filter flows by origin/destination nodes
        origin_node_ids = indicator_flow.origin_node_ids
        origin_node_ids = origin_node_ids.split(',') \
                if len(origin_node_ids) > 0 else []
        destination_node_ids = indicator_flow.destination_node_ids
        destination_node_ids = destination_node_ids.split(',') \
                if len(destination_node_ids) > 0 else []
        origins = self.get_actors(origin_node_ids,
                                      indicator_flow.origin_node_level)
        destinations = self.get_actors(destination_node_ids,
                                           indicator_flow.destination_node_level)

        if geom:
            spatial = indicator_flow.spatial_application.name
            if spatial == 'ORIGIN' or spatial == 'BOTH':
                origins = filter_actors_by_area(origins, geom)
            if spatial == 'DESTINATION' or spatial == 'BOTH':
                destinations = filter_actors_by_area(destinations, geom)

        flows = flows.filter(
                Q(origin__in=origins) & Q(destination__in=destinations))
        return flows

    def sum(self, flows, field='statusquo_amount'):
        '''sum up flow amounts'''
        # sum up amounts to single value
        if len(flows) == 0:
            return 0
        amount = flows.aggregate(amount=Sum(field))['amount'] or 0
        return amount

    def get_actors(self, node_ids, node_level):
        actors = Actor.objects.all()
        if len(node_ids) > 0:
            filter_prefix = ''
            if node_level.name == 'ACTIVITY':
                filter_prefix = 'activity__'
            if node_level.name == 'ACTIVITYGROUP':
                filter_prefix = 'activity__activitygroup__'
            kwargs = {filter_prefix + 'id__in': node_ids}
            actors = actors.filter(**kwargs)
        return actors

    def calculate(self, indicator, areas=[], geom=None, aggregate=False):
        ''' calculate Indicator by filtering and aggregating flows

        Parameters
        ----------
            indicator_flow : IndicatorFlow
                indicator flow used for filtering flows
            geom : dict, optional
                geoJSON with geometry of an area, filter and calculate for this
                area
            areas : list of Area, optional
                filter and calculate for each area seperately
            aggregate : str, optional
                aggregate the calculated amounts to single amount
                (only when calculating areas)

        Returns
        -------
           amounts: list of OrderedDict
              keys area, value and delta, value of 'area' is area id,
              value of 'value' is (aggregated) value of area, 'delta' is
              aggregated difference to status quo;
              area = -1 if not associated to a specific area, (e.g. when
              aggregating areas)
        '''
        raise NotImplementedError

    def calculate_indicator_flow(self, indicator_flow, areas=[],
                                 geom=None, aggregate=False, func='sum'):
        ''' calculate single IndicatorFlow by filtering and aggregating flows

        Parameters
        ----------
            indicator_flow : IndicatorFlow
                indicator flow used for filtering flows
            geom : dict, optional
                geoJSON with geometry of an area, filter and calculate for this
                area
            areas : list of Area, optional
                filter and calculate for each area seperately
            func : str,
                name of class method to aggregate flows (default is 'sum'),
                addressed method has to have queryset of FractionFlow as
                single parameter
            aggregate : str, optional
                aggregate the calculated amounts to single amount
                (only when calculating areas)

        Returns
        -------
           amounts: dict,
              keys area area ids, values are the tuples of calculated amounts
              and the amounts in strategy (if there is one, else 0)
              key = -1 if not associated to a specific area, (e.g. when
              aggregating areas)
        '''

        agg_func = getattr(self, func)
        # single value (nothing to iterate)
        if (not areas or len(areas)) == 0 and not geom:
            flows = self.get_queryset(indicator_flow, geom=geom)
            amount = agg_func(flows)
            strategy_amount = agg_func(flows, field='strategy_amount') \
                if self.strategy else 0
            return {-1: (amount, strategy_amount)}
        amounts = {}
        geometries = []
        if geom:
            geometries.append(('geom', geom))
        for area in areas:
            geom = area.geom
            geometries.append((area.id, geom))
        for g_id, geometry in geometries:
            flows = self.get_queryset(indicator_flow, geom=geometry)
            amount = agg_func(flows)
            strategy_amount = agg_func(flows, field='strategy_amount') \
                if self.strategy else 0
            amounts[g_id] = (amount, strategy_amount)
        if aggregate:
            total_sum = 0
            total_strategy_amount = 0
            for a in amounts.values():
                total_sum += a[0]
                total_strategy_amount += a[1]
            return {-1: (total_sum, total_strategy_amount)}
        return amounts


class IndicatorA(ComputeIndicator):
    ''' Aggregated Flow A '''
    description = _('SUM aggregation Flow A')
    name = _('Flow A')
    default_unit = _('t / year')

    def calculate(self, indicator, areas=[], geom=None, aggregate=False):
        amounts = self.calculate_indicator_flow(
            indicator.flow_a, areas=areas, geom=geom, aggregate=aggregate,
            func='sum')
        results = [OrderedDict({
            'area': area_id,
            'value': amount[1] if self.strategy else amount[0],
            'delta': amount[1] - amount[0] if self.strategy else None
        }) for area_id, amount in amounts.items()]
        return results


class IndicatorAB(ComputeIndicator):
    ''' Aggregated Flow A / aggregated Flow B '''
    description = _('SUM aggregation Flow A / SUM aggregation Flow B')
    name = _('(Flow A / Flow B) * 100')
    default_unit = '%'

    def calculate(self, indicator, areas=[], geom=None, aggregate=False):
        result_a = self.calculate_indicator_flow(
            indicator.flow_a, areas=areas, geom=geom,
            aggregate=aggregate, func='sum')
        result_b = self.calculate_indicator_flow(
            indicator.flow_b, areas=areas, geom=geom,
            aggregate=aggregate, func='sum')

        result_merged = []
        area_ids = np.unique(list(result_a.keys()) + list(result_b.keys()))

        for area_id in area_ids:
            sum_a = result_a.get(area_id, (0, 0))
            sum_b = result_b.get(area_id, (0, 0))
            amount = 100 * sum_a[0] / sum_b[0] if sum_b[0] > 0 else None
            if self.strategy:
                strategy_amount = 100 * sum_a[1] / sum_b[1] if sum_b[1] > 0 else None
                if (strategy_amount is None or amount is None):
                    delta = None
                else:
                    delta = strategy_amount - amount
                amount = strategy_amount
            else:
                delta = None
            result_merged.append(OrderedDict({
                'area': area_id,
                'value': amount,
                'delta': delta
            }))
        return result_merged


class IndicatorInhabitants(IndicatorAB):
    description = _('SUM aggregation Flow A / Inhabitants in Area')
    name = _('Flow A / Inhabitants')
    default_unit = _('kg / inhabitant and year')

    def calculate(self, indicator, areas=[], geom=None, aggregate=False):
        amounts = self.calculate_indicator_flow(
            indicator.flow_a, areas=areas, geom=geom, aggregate=aggregate,
            func='sum')
        total_inhabitants = 0
        area_inhabitants = {}
        for area in areas:
            inh = area.inhabitants
            total_inhabitants += inh
            area_inhabitants[area.id] = inh
        # ToDo: how to calc for geometries?
        #       inhabitant data is attached to the areas only
        area_inhabitants['geom'] = 0
        area_inhabitants[-1] = total_inhabitants

        results = []

        for area, amount in amounts.items():
            inh = area_inhabitants[area]
            res = 1000 * amount[0] / inh if inh > 0 else None
            if self.strategy:
                strategy_res = 1000 * amount[1] / inh if inh > 0 else None
                if (strategy_res is None or amount is None):
                    delta = None
                else:
                    delta = strategy_res - res
                res = strategy_res
            else:
                delta = None
            results.append(OrderedDict({
                'area': area,
                'value': res,
                'delta': delta
            }))

        return results


class IndicatorArea(ComputeIndicator):
    description = _('SUM aggregation Flow A / geometrical area in hectar')
    name = _('Flow A / Area (ha)')
    default_unit = _('t / hectar and year')

    def calculate(self, indicator, areas=[], geom=None, aggregate=False):
        amounts = self.calculate_indicator_flow(
            indicator.flow_a, areas=areas, geom=geom, aggregate=aggregate,
            func='sum')
        total_ha = 0
        areas_ha = {}
        for area in areas:
            ha = area.ha
            total_ha += ha
            areas_ha[area.id] = ha
        if geom:
            geom = GEOSGeometry(geom)
            sm = geom.transform(3035, clone=True).area
            ha = sm / 10000
            total_ha += ha
            areas_ha['geom'] = ha
        areas_ha[-1] = total_ha

        results = []

        for area_id, amount in amounts.items():
            ha = areas_ha[area_id]
            res = amount[0] / ha if ha > 0 else None
            if self.strategy:
                strategy_res = amount[1] / ha if ha > 0 else None
                if (strategy_amount is None or amount is None):
                    delta = None
                else:
                    delta = strategy_res - res
                res = strategy_res
            else:
                delta = None
            results.append(OrderedDict({
                'area': area_id,
                'value': res,
                'delta': delta
            }))

        return results


class FlowIndicatorViewSet(RevisionMixin, CasestudyViewSetMixin,
                           ModelPermissionViewSet):
    '''
    view on indicators in db
    '''
    queryset = FlowIndicator.objects.order_by('id')
    serializer_class = FlowIndicatorSerializer

    def destroy(self, request, **kwargs):
        instance = FlowIndicator.objects.get(id=kwargs['pk'])
        for flow in [instance.flow_a, instance.flow_b]:
            if flow:
                flow.delete()
        return super().destroy(request, **kwargs)

    @action(methods=['get', 'post'], detail=True)
    def compute(self, request, **kwargs):
        self.check_permission(request, 'view')
        indicator = self.get_queryset().get(id=kwargs.get('pk', None))
        query_params = request.query_params
        body_params = request.data
        if not indicator:
            raise Http404
        typ = indicator.indicator_type
        compute_class = globals().get(typ.name, None)
        assert issubclass(compute_class, ComputeIndicator)
        geom = body_params.get('geom', None) or query_params.get('geom', None)
        if geom == 'null':
            geom = None
        areas = (body_params.get('areas', None) or
                 query_params.get('areas', None))
        aggregate = (body_params.get('aggregate', None) or
                     query_params.get('aggregate', None))
        strategy = (body_params.get('strategy', None) or
                    query_params.get('strategy', None))
        if strategy:
            strategy = Strategy.objects.get(id=strategy)
            if strategy.status == 0:
                return HttpResponseBadRequest(
                    _('calculation is not done yet'))
            if strategy.status == 1:
                return HttpResponseBadRequest(
                    _('calculation is still in process'))
        compute = compute_class(strategy=strategy)
        if aggregate is not None:
            aggregate = aggregate.lower() == 'true'
        if areas:
            areas = areas.split(',')
            areas = Area.objects.filter(id__in=areas)
        values = compute.calculate(indicator, areas=areas or [], geom=geom,
                                  aggregate=aggregate)
        return Response(values)

    def get_queryset(self):
        keyflow_pk = self.kwargs.get('keyflow_pk')
        queryset = self.queryset
        if keyflow_pk is not None:
            queryset = queryset.filter(keyflow__id=keyflow_pk)
        return queryset

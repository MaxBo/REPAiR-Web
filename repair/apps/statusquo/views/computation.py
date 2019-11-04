from abc import ABCMeta
import numpy as np
from django.db.models import Q, Sum, Case, When, F, Value
from collections import OrderedDict
from django.utils.translation import ugettext as _
from django.contrib.gis.geos import GEOSGeometry
from django.db.models.functions import Coalesce

from repair.apps.utils.utils import descend_materials
from repair.apps.asmfa.models import (Actor, FractionFlow, Process,
                                      AdministrativeLocation, Material)
from repair.apps.asmfa.serializers import Actor2ActorSerializer
from repair.apps.utils.utils import get_annotated_fractionflows

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
    is_absolute = True

    def __init__(self, keyflow_pk, strategy=None):
        self.keyflow_pk = keyflow_pk
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

        flows = get_annotated_fractionflows(self.keyflow_pk,
                                            strategy_id=self.strategy.id)

        # filter flows by type (waste/product/both)
        if flow_type != 'BOTH':
            is_waste = True if flow_type == 'WASTE' else False
            flows = flows.filter(strategy_waste=is_waste)
        if hazardous != 'BOTH':
            is_hazardous = True if hazardous == 'YES' else False
            flows = flows.filter(strategy_hazardous=is_hazardous)
        if avoidable != 'BOTH':
            is_avoidable = True if avoidable == 'YES' else False
            flows = flows.filter(avoidable=is_avoidable)

        # filter flows by processes
        process_ids = indicator_flow.process_ids
        if (process_ids):
            process_ids = process_ids.split(',')
            processes = Process.objects.filter(id__in=process_ids)
            flows = flows.filter(strategy_process__in=processes)

        if materials:
            mats = descend_materials(list(materials))
            mats = Material.objects.filter(id__in=mats)
            flows = flows.filter(strategy_material__in=mats)

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

    def sum(self, flows, field='amount'):
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
            amount = agg_func(flows, field='amount')
            strategy_amount = agg_func(flows, field='strategy_amount')
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
            amount = agg_func(flows, field='amount')
            strategy_amount = agg_func(flows, field='strategy_amount')
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
    is_absolute = True

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
    is_absolute = False

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
    is_absolute = True

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
    is_absolute = True

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
                if (strategy_res is None or amount is None):
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

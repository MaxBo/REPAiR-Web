from reversion.views import RevisionMixin
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnList
from rest_framework.decorators import action
from django.http import Http404
from abc import ABCMeta
from enum import Enum
import numpy as np
from django.db.models import Q, Sum
from collections import OrderedDict
from django.utils.translation import ugettext as _
from repair.apps.asmfa.views import descend_materials
from repair.apps.utils.views import (ModelPermissionViewSet,
                                     CasestudyViewSetMixin)
from repair.apps.asmfa.models import Actor, FractionFlow, AdministrativeLocation
from repair.apps.asmfa.serializers import Actor2ActorSerializer
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
    def sum(self, indicator_flow, geom=None):
        '''
        aggregation sum
        '''
        materials = indicator_flow.materials.all()
        flow_type = indicator_flow.flow_type.name
        hazardous = indicator_flow.hazardous.name
        avoidable = indicator_flow.avoidable.name

        # filter flows by type (waste/product/both)
        flows = FractionFlow.objects.filter()
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
            flows.filter(process__id__in=process_ids)

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

        if materials:
            mats = descend_materials(list(materials))
            flows = flows.filter(material__id__in=mats)

        # sum up amounts to single value
        amount = flows.aggregate(amount=Sum('amount'))['amount'] or 0
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

    def filter_by_area(self, actors, area):
        return actors


class IndicatorA(ComputeIndicator):
    '''
    Aggregated Flow A
    '''
    description = _('SUM aggregation Flow A')
    name = _('Flow A')
    default_unit = _('t / year')

    def process(self, indicator, areas=[], geom=None, aggregate=False):
        flow_a = indicator.flow_a
        if not areas and not geom:
            amount = self.sum(flow_a)
            return [OrderedDict({'area': -1, 'value': amount})]
        amounts = []
        if geom:
            amount = self.sum(flow_a, geom) if flow_a else 0
            amounts.append(OrderedDict({'area': 'geom', 'value': amount}))
        for area in areas:
            geom = Area.objects.get(id=area).geom
            amount = self.sum(flow_a, geom) if flow_a else 0
            amounts.append(OrderedDict({'area': area, 'value': amount}))
        if aggregate:
            total_sum = 0
            for a in amounts:
                total_sum += a['value']
            return [OrderedDict({'area': -1, 'value': total_sum})]
        return amounts


class IndicatorAB(ComputeIndicator):
    '''
    Aggregated Flow A / aggregated Flow B
    '''
    description = _('SUM aggregation Flow A / SUM aggregation Flow B')
    name = _('(Flow A / Flow B) * 100')
    default_unit = '%'

    def process(self, indicator, areas=[], geom=None, aggregate=False):
        flow_a = indicator.flow_a
        flow_b = indicator.flow_b
        if not areas and not geom:
            amount = self.sum(flow_a) / self.sum(flow_b)
            return [OrderedDict({'area': -1, 'value': amount})]
        amounts = []
        total_sum_a = 0
        total_sum_b = 0
        if geom:
            if flow_a and flow_b:
                sum_a = self.sum(flow_a, geom)
                # ToDo: what if sum_b = 0?
                sum_b = self.sum(flow_b, geom)
                total_sum_a += sum_a
                total_sum_b += sum_b
                amount = 100 * sum_a / sum_b if sum_b > 0 else 0
            else:
                amount = 0
            amounts.append(OrderedDict({'area': 'geom', 'value': amount}))
        for area in areas:
            if flow_a and flow_b:
                geom = Area.objects.get(id=area).geom
                sum_a = self.sum(flow_a, geom)
                # ToDo: what if sum_b = 0?
                sum_b = self.sum(flow_b, geom)
                total_sum_a += sum_a
                total_sum_b += sum_b
                amount = 100 * sum_a / sum_b if sum_b > 0 else 0
            else:
                amount = 0
            amounts.append(OrderedDict({'area': area, 'value': amount}))
        if aggregate:
            amount = 100 * total_sum_a / total_sum_b if total_sum_b > 0 else 0
            return [OrderedDict({'area': -1, 'value': amount})]
        return amounts


# ToDo: almost same as IndicatorAB, subclass this
class IndicatorInhabitants(ComputeIndicator):
    description = _('SUM aggregation Flow A / Inhabitants in Area')
    name = _('Flow A / Inhabitants')
    default_unit = _('t / inhabitant and year')

    def process(self, indicator, areas=[], geom=None, aggregate=False):
        if not areas and not geom:
            return [OrderedDict({'area': -1, 'value': 0})]
        amounts = []
        #  ToDo: how to calc for geometries?
        #        inhabitant data is attached to the areas only
        if geom:
            amounts.append(OrderedDict({'area': 'geom', 'value': 0}))
        total_sum_a = 0
        total_sum_b = 0
        flow_a = indicator.flow_a
        for area_id in areas:
            if flow_a:
                area = Area.objects.get(id=area_id)
                geom = area.geom
                sum_a = self.sum(flow_a, geom)
                # ToDo: what if sum_b = 0?
                sum_b = area.inhabitants
                total_sum_a += sum_a
                total_sum_b += sum_b
                amount = sum_a / sum_b if sum_b > 0 else 0
            else:
                amount = 0
            amounts.append(OrderedDict({'area': area_id, 'value': amount}))
        if aggregate:
            amount = total_sum_a / total_sum_b if total_sum_b > 0 else 0
            return [OrderedDict({'area': -1, 'value': amount})]
        return amounts


# ToDo: almost same as IndicatorAB, subclass this
class IndicatorArea(ComputeIndicator):
    description = _('SUM aggregation Flow A / geometrical area in hectar')
    name = _('Flow A / Area (ha)')
    default_unit = _('t / hectar and year')

    def process(self, indicator, areas=[], geom=None, aggregate=False):
        if not areas and not geom:
            return [OrderedDict({'area': -1, 'value': 0})]
        amounts = []
        if geom:
            sm = geom.transform(3035, clone=True).area
            ha = sm / 10000
            amounts.append(OrderedDict({'area': 'geom', 'value': ha}))
        total_sum_a = 0
        total_ha = 0
        flow_a = indicator.flow_a
        for area_id in areas:
            if flow_a:
                area = Area.objects.get(id=area_id)
                geom = area.geom
                sm = area.geom.transform(3035, clone=True).area
                sum_a = self.sum(flow_a, geom)
                # ToDo: what if sum_b = 0?
                ha = sm / 10000
                total_sum_a += sum_a
                total_ha += ha
                amount = sum_a / ha if ha > 0 else 0
            else:
                amount = 0
            amounts.append(OrderedDict({'area': area_id, 'value': amount}))
        if aggregate:
            amount = total_sum_a / total_ha if total_ha > 0 else 0
            return [OrderedDict({'area': -1, 'value': amount})]
        return amounts


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
        computer_class = globals().get(typ.name, None)
        assert issubclass(computer_class, ComputeIndicator)
        computer = computer_class()
        geom = body_params.get('geom', None) or query_params.get('geom', None)
        areas = (body_params.get('areas', None) or
                 query_params.get('areas', None))
        aggregate = (body_params.get('aggregate', None) or
                     query_params.get('aggregate', None))
        if aggregate is not None:
            aggregate = aggregate.lower() == 'true'
        if areas:
            areas = areas.split(',')
        values = computer.process(indicator, areas=areas or [], geom=geom,
                                  aggregate=aggregate)
        return Response(values)

    def get_queryset(self):
        keyflow_pk = self.kwargs.get('keyflow_pk')
        queryset = self.queryset
        if keyflow_pk is not None:
            queryset = queryset.filter(keyflow__id=keyflow_pk)
        return queryset

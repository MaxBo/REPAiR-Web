from reversion.views import RevisionMixin
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnList
from rest_framework.decorators import action
from django.http import Http404
from abc import ABCMeta
from enum import Enum
import numpy as np
from django.db.models import Q
from collections import OrderedDict
from django.utils.translation import ugettext as _

from repair.apps.utils.views import (ModelPermissionViewSet,
                                     CasestudyViewSetMixin)
from repair.apps.asmfa.models import Actor, Actor2Actor, AdministrativeLocation
from repair.apps.asmfa.serializers import Actor2ActorSerializer
from repair.apps.asmfa.views import aggregate_fractions
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
    def sum(self, indicator_flow, geom=None):
        '''
        aggregation sum
        '''
        materials = indicator_flow.materials.all()
        flow_type = indicator_flow.flow_type.name

        # filter flows by type (waste/product/both)
        flows = Actor2Actor.objects.filter()
        if flow_type != 'BOTH':
            is_waste = True if flow_type == 'WASTE' else False
            flows = flows.filter(waste=is_waste)

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

        # serialize and aggregate materials (incl. recalc. of amounts)
        serializer = Actor2ActorSerializer(flows, many=True)
        data = serializer.data
        if (len(materials) > 0):
            aggregate_fractions(materials, data, aggregate_materials=True)

        # sum up amounts to single value
        amount = 0
        for flow in data:
            amount += flow['amount']
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
    def process(self, indicator, areas=[], geom=None):
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
        return amounts


class IndicatorAB(ComputeIndicator):
    '''
    Aggregated Flow A / aggregated Flow B
    '''
    description = _('SUM aggregation Flow A / SUM aggregation Flow B')
    name = _('Flow A / Flow B')
    def process(self, indicator, areas=[], geom=None):
        flow_a = indicator.flow_a
        flow_b = indicator.flow_b
        if not areas and not geom:
            amount = self.sum(flow_a) / self.sum(flow_b)
            return [OrderedDict({'area': -1, 'value': amount})]
        amounts = []
        if geom:
            if flow_a and flow_b:
                sum_a = self.sum(flow_a, geom)
                # ToDo: what if sum_b = 0?
                sum_b = self.sum(flow_b, geom)
                amount = sum_a / sum_b if sum_b > 0 else 0
            else:
                amount = 0
            amounts.append(OrderedDict({'area': 'geom', 'value': amount}))
        for area in areas:
            if flow_a and flow_b:
                geom = Area.objects.get(id=area).geom
                sum_a = self.sum(flow_a, geom)
                # ToDo: what if sum_b = 0?
                sum_b = self.sum(flow_b, geom)
                amount = sum_a / sum_b if sum_b > 0 else 0
            else:
                amount = 0
            amounts.append(OrderedDict({'area': area, 'value': amount}))
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
        if areas:
            areas = areas.split(',')
        values = computer.process(indicator, areas=areas or [], geom=geom)
        return Response(values)

    def get_queryset(self):
        keyflow_pk = self.kwargs.get('keyflow_pk')
        queryset = self.queryset
        if keyflow_pk is not None:
            queryset = queryset.filter(keyflow__id=keyflow_pk)
        return queryset

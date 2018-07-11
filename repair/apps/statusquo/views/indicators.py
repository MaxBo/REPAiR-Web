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

from repair.apps.utils.views import ModelPermissionViewSet
from repair.apps.asmfa.models import Actor, Actor2Actor, AdministrativeLocation
from repair.apps.asmfa.serializers import Actor2ActorSerializer
from repair.apps.asmfa.views import aggregate_fractions
from repair.apps.statusquo.models import FlowIndicator, IndicatorType
from repair.apps.statusquo.serializers import FlowIndicatorSerializer
from repair.apps.studyarea.models import Area


def filter_actors_by_area(actors, area):
    '''
    get actors in an area (by administrative location)
    '''
    locations = AdministrativeLocation.objects.filter(actor__in=actors)
    locations = locations.filter(geom__intersects=area.geom)
    actors_in_area = actors.filter(id__in=locations.values('actor'))
    return actors_in_area


class ComputeIndicator(metaclass=ABCMeta):
    '''
    abstract class for computing indicators
    '''
    def sum(self, indicator_flow, area=None):
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

        if area:
            area = Area.objects.get(id=area)
            spatial = indicator_flow.spatial_application.name
            if spatial == 'ORIGIN' or spatial == 'BOTH':
                origins = filter_actors_by_area(origins, area)
            if spatial == 'DESTINATION' or spatial == 'BOTH':
                destinations = filter_actors_by_area(destinations, area)
        
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
    def process(self, indicator, areas=None):
        flow_a = indicator.flow_a
        if not areas:
            amount = self.sum(flow_a)
            return [OrderedDict({'area': -1, 'value': amount})]
        amounts = []
        for area in areas:
            amount = self.sum(flow_a, area)
            amounts.append(OrderedDict({'area': area, 'value': amount}))
        return amounts


class IndicatorAB(ComputeIndicator):
    '''
    Aggregated Flow A / aggregated Flow B
    '''
    def process(self):
        flow_a = indicator.flow_a
        flow_b = indicator.flow_b
        if not areas:
            amount = self.sum(flow_a) / self.sum(flow_b)
            return [OrderedDict({'area': -1, 'value': amount})]
        amounts = []
        for area in areas:
            amount = self.sum(flow_a, area) / self.sum(flow_b, area)
            amounts.append(OrderedDict({'area': area, 'value': amount}))
        return amounts


class ComputeIndicators(Enum):
    A = IndicatorA
    AB = IndicatorAB

# make sure that the indicators to compute
# match the indicators how they are stored in db
assert (np.array_equal(np.sort(ComputeIndicators._member_names_),
                       np.sort(IndicatorType._member_names_))), \
       "ComputeIndicators and IndicatorTypes don't match"


class FlowIndicatorViewSet(RevisionMixin, ModelPermissionViewSet):
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

    @action(methods=['get'], detail=True)
    def compute(self, request, **kwargs):
        indicator = self.get_queryset().get(id=kwargs.get('pk', None))
        if not indicator:
            raise Http404
        typ = indicator.indicator_type
        computer = ComputeIndicators[typ.name].value()
        areas = request.query_params.get('areas', None)
        if areas:
            areas = areas.split(',')
        values = computer.process(indicator, areas)
        return Response(values)
    
    def get_queryset(self):
        keyflow_pk = self.kwargs.get('keyflow_pk')
        queryset = self.queryset
        if keyflow_pk is not None:
            queryset = queryset.filter(keyflow__id=keyflow_pk)
        return queryset
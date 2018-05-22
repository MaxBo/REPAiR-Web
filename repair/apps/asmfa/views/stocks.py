# API View
from abc import ABC
from reversion.views import RevisionMixin
from rest_framework.response import Response
import numpy as np

from repair.apps.asmfa.models import (
    GroupStock,
    ActivityStock,
    ActorStock,
    Material
)

from repair.apps.asmfa.serializers import (
    GroupStockSerializer,
    ActivityStockSerializer,
    ActorStockSerializer,
)

from repair.apps.asmfa.views import filter_by_material, process_data_fractions

from repair.apps.login.views import CasestudyViewSetMixin
from repair.apps.utils.views import ModelPermissionViewSet


class StockViewSet(RevisionMixin,
                  CasestudyViewSetMixin,
                  ModelPermissionViewSet,
                  ABC):
    
    def list(self, request, **kwargs):
        self.check_permission(request, 'view')
        SerializerClass = self.get_serializer_class()
        query_params = request.query_params
        queryset = self.get_queryset()
        materials = None
        
        filter_waste = 'waste' in query_params.keys()
        filter_nodes = ('nodes' in query_params.keys() or
                        'nodes[]' in query_params.keys())
        filter_material = 'material' in query_params.keys()
        aggregate = ('aggregated' in query_params.keys() and
                     query_params['aggregated'] in ['true', 'True'])
        
        # do the filtering and serializing of superclass, if none of the above
        # filters are queried (unfortunately they all conflict with filters of 
        # superclass CasestudyViewSetMixin)
        if not np.any([filter_waste, filter_nodes, filter_material, aggregate]):
            return super().list(request, **kwargs)

        # filter products (waste=False) or waste (waste=True)
        if filter_waste:
            queryset = queryset.filter(waste=query_params.get('waste'))
        
        # filter by origins AND destinations
        if filter_nodes:
            nodes = (query_params.get('nodes', None)
                     or request.GET.getlist('nodes[]')) 
            queryset = queryset.filter(origin__in=nodes)
            
        # filter the flows by their fractions excluding flows whose
        # fractions don't contain the requested material (incl. child materials)
        if filter_material:
            try:
                material = Material.objects.get(id=query_params['material'])
            except Material.DoesNotExist:
                return Response(status=404)
            materials = [material]
            queryset = filter_by_material(material, queryset)

        serializer = SerializerClass(queryset, many=True,
                                         context={'request': request, })
        data = serializer.data
    
        # if the fractions of flows are filtered by material, the other
        # fractions should be removed from the returned data
        if filter_material and not aggregate:
            process_data_fractions(materials, data, aggregate=False)
            return Response(data)
    
        # aggregate the fractions of the queryset
        if aggregate:
            # no material was requested -> aggregate by top level materials
            # else take the materials from if-clause 'filter_material'
            if materials is None:
                materials = Material.objects.filter(parent__isnull=True)
    
            #aggregate_queryset(materials, queryset)
            #filtered = True
    
            process_data_fractions(materials, data, aggregate=True)
            return Response(data)
    
        return Response(data)
    
    def get_queryset(self):
        model = self.serializer_class.Meta.model
        return model.objects.\
               select_related('keyflow__casestudy').\
               select_related('publication').\
               select_related("origin").\
               prefetch_related("composition__fractions").\
               all()
    

class GroupStockViewSet(StockViewSet):
    add_perm = 'asmfa.add_groupstock'
    change_perm = 'asmfa.change_groupstock'
    delete_perm = 'asmfa.delete_groupstock'
    queryset = GroupStock.objects.all()
    serializer_class = GroupStockSerializer


class ActivityStockViewSet(StockViewSet):
    add_perm = 'asmfa.add_activitystock'
    change_perm = 'asmfa.change_activitystock'
    delete_perm = 'asmfa.delete_activitystock'
    queryset = ActivityStock.objects.all()
    serializer_class = ActivityStockSerializer


class ActorStockViewSet(StockViewSet):
    add_perm = 'asmfa.add_actorstock'
    change_perm = 'asmfa.change_actorstock'
    delete_perm = 'asmfa.delete_actorstock'
    queryset = ActorStock.objects.all()
    serializer_class = ActorStockSerializer
    additional_filters = {'origin__included': True}

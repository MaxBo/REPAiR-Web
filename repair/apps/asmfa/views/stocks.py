# API View
from abc import ABC
from reversion.views import RevisionMixin
from rest_framework.response import Response

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

from repair.apps.asmfa.views import filter_by_material

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
        filtered = None
        if 'material' in query_params.keys():
            queryset = filtered or self.queryset
            try:
                material = Material.objects.get(id=query_params['material'])
            except Material.DoesNotExist:
                return Response(status=404)
            filtered = filter_by_material(material, self.queryset)
        if 'waste' in query_params.keys():
            queryset = filtered if filtered is not None else self.queryset
            filtered = queryset.filter(waste=query_params.get('waste'))
        if 'nodes' in query_params.keys() or 'nodes[]' in query_params.keys():
            queryset = filtered if filtered is not None else self.queryset
            nodes = (query_params.get('nodes', None)
                     or request.GET.getlist('nodes[]')) 
            filtered = queryset.filter(origin__in=nodes)
        if filtered is not None:
            serializer = SerializerClass(filtered, many=True,
                                         context={'request': request, })
            return Response(serializer.data)
        return super().list(request, **kwargs)
    

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

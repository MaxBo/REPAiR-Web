# API View
from abc import ABC
from reversion.views import RevisionMixin
from rest_framework.response import Response
from django.db.models import Q
import numpy as np
import json

from repair.apps.asmfa.models import (
    GroupStock,
    ActivityStock,
    ActorStock,
    Material,
    Actor
)

from repair.apps.asmfa.serializers import (
    GroupStockSerializer,
    ActivityStockSerializer,
    ActorStockSerializer,
)

from repair.apps.asmfa.views import (filter_by_material, aggregate_fractions,
                                     aggregate_to_level)

from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet,
                                     PostGetViewMixin)


class StockViewSet(RevisionMixin,
                   CasestudyViewSetMixin,
                   ModelPermissionViewSet,
                   ABC):
    
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


class ActorStockViewSet(PostGetViewMixin, StockViewSet):
    add_perm = 'asmfa.add_actorstock'
    change_perm = 'asmfa.change_actorstock'
    delete_perm = 'asmfa.delete_actorstock'
    queryset = ActorStock.objects.all()
    serializer_class = ActorStockSerializer
    additional_filters = {'origin__included': True}

    def post_get(self, request, **kwargs):
        '''
        body params:
        body = {
            waste: true / false,  # products or waste, don't pass for both
            
            # filter/aggregate by given material 
            materials: {
                ids: id, # ids of materials to filter, only flows with those materials and their children will be returned, other materials will be ignored
                aggregate: true / false, # if true the children of the given materials will be aggregated, aggregates to top level materials if no ids were given
            },
            
            filter_link: and/or, # logical linking of filters, defaults to 'or'
            
            # prefilter stocks
            filters: [
                {
                     function: django filter function (e.g. origin__id__in)
                     values: values for filter function (e.g. [1,5,10])
                },
                ...
            ],
            
        }
        '''
        self.check_permission(request, 'view')
        SerializerClass = self.get_serializer_class()
        params = {}
        # values of body keys are not parsed
        for key, value in request.data.items():
            try:
                params[key] = json.loads(value)
            except json.decoder.JSONDecodeError:
                params[key] = value
        queryset = self.get_queryset()

        waste_filter = params.get('waste', None)
        filters = params.get('filters', None)
        filter_link = params.get('filter_link', None)
        material_filter = params.get('material', None)
        level_aggregation = params.get('aggregation_level', None)

        # filter products (waste=False) or waste (waste=True)
        if waste_filter is not None:
            queryset = queryset.filter(waste=waste_filter)
    
        # filter queryset based on passed filters
        if filters:
            filter_functions = []
            for f in filters:
                func = f['function']
                v = f['values']
                filter_function = Q(**{func: v})
                filter_functions.append(filter_function)
            if filter_link == 'and':
                link_func = np.bitwise_and
            else:
                link_func = np.bitwise_or
            if len(filter_functions) == 1:
                queryset = queryset.filter(filter_functions[0])
            if len(filter_functions) > 1:
                queryset = queryset.filter(link_func(*filter_functions))
        
        aggregate_materials = (False if material_filter is None
                                   else material_filter.get('aggregate', False))
        material_ids = (None if material_filter is None
                            else material_filter.get('ids', None))
        unaltered_material_ids = ([] if material_filter is None
                                  else material_filter.get('unaltered', []))
    
        materials = None
        unaltered_materials = None
        # filter the stocks by their fractions excluding flows whose
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
        
        if level_aggregation and level_aggregation != 'actors':
            data = aggregate_to_level(data, queryset, level_aggregation, None,
                                      is_stock=True)
        
        # materials were given and/or materials shall be aggregated
        if materials or aggregate_materials:
            data = aggregate_fractions(
                materials, data, aggregate_materials=aggregate_materials,
                unaltered_materials=unaltered_materials
            )
            return Response(data)
        
        return Response(data)


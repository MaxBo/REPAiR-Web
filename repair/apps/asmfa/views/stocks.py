# API View
from abc import ABC
from reversion.views import RevisionMixin
from rest_framework.response import Response
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

from repair.apps.asmfa.views import (filter_by_material, process_data_fractions,
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
            material: {
                aggregate: true / false, # aggregate child materials
                                         # to level of given material
                                         # or to top level if no id is given
                id: id, # id of material
            },
            
            subset: {
                # filter origin actors by their ids OR by group/activity ids (you may do
                # all the same time, but makes not much sense though)
                activitygroups: [...], # ids of activitygroups
                activities: [...], # ids of activities
                ids = [...] # ids of the actors
                
            },
            
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
        subset_filter = params.get('subset', None)
        material_filter = params.get('material', None)
        level_aggregation = params.get('aggregation_level', None)

        # filter products (waste=False) or waste (waste=True)
        if waste_filter is not None:
            queryset = queryset.filter(waste=waste_filter)
    
        # build subset of origins
        if subset_filter:
            group_ids = subset_filter.get('activitygroups', None)
            activity_ids = subset_filter.get('activities', None)
            actor_ids = subset_filter.get('actors', None)
            direction = subset_filter.get('direction', 'both')
            
            actors = Actor.objects.all()
            if group_ids:
                actors = actors.filter(activity__activitygroup__id__in=group_ids)
            if activity_ids:
                actors = actors.filter(activity__id__in=activity_ids)
            if actor_ids:
                actors = actors.filter(id__in=actor_ids)
            queryset = queryset.filter(origin__in=actors)
        
        aggregate_materials = (False if material_filter is None
                                   else material_filter.get('aggregate', False))
        material_id = (None if material_filter is None
                           else material_filter.get('id', None))
        material = None
        
        # filter the flows by their fractions excluding flows whose
        # fractions don't contain the requested material (incl. child materials)
        if material_id is not None:
            try:
                material = Material.objects.get(id=material_filter['id'])
            except Material.DoesNotExist:
                return Response(status=404)
            queryset = filter_by_material(material, queryset)
        
        serializer = SerializerClass(queryset, many=True,
                                         context={'request': request, })
        data = serializer.data
    
        # POSTPROCESSING: all following operations are performed on serialized
        # data
        
        if level_aggregation and level_aggregation != 'actors':
            data = aggregate_to_level(data, queryset, level_aggregation, None,
                                      is_stock=True)
        
        # if the fractions of stocks are filtered by material, the other
        # fractions should be removed from the returned data        
        if material and not aggregate_materials:
            # if the fractions of flows are filtered by material, the other
            # fractions should be removed from the returned data
            if not aggregate_materials:
                data = process_data_fractions(material, material.children,
                                              data, aggregate_materials=False)
                return Response(data)

        # aggregate the fractions of the queryset
        if aggregate_materials:
            # aggregate the fractions of the queryset
            # take the material and its children from if-clause 'filter_material'
            if material:
                childmaterials = material.children
            # no material was requested -> aggregate by top level materials
            if material is None:
                childmaterials = Material.objects.filter(parent__isnull=True)

            data = process_data_fractions(material, childmaterials, data,
                                          aggregate_materials=True)
            return Response(data)

        return Response(data)


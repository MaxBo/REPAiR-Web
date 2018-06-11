from django.core.exceptions import ObjectDoesNotExist
from rest_framework import exceptions
from django.contrib.gis.db.models.functions import PointOnSurface, AsGeoJSON

from repair.apps.login.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet)

from repair.apps.studyarea.models import (AdminLevels,
                                          Area,
                                          Areas,
                                          )

from repair.apps.studyarea.serializers import (AdminLevelSerializer,
                                               AreaSerializer,
                                               AreaGeoJsonSerializer,
                                               AreaGeoJsonPostSerializer,
                                               )


class AdminLevelViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    queryset = AdminLevels.objects.all()
    serializer_class = AdminLevelSerializer


class AreaViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    serializers = {'retrieve': AreaGeoJsonSerializer,
                   'update': AreaGeoJsonSerializer,
                   'partial_update': AreaGeoJsonSerializer,
                   'create': AreaGeoJsonPostSerializer, }

    def _filter(self, lookup_args, query_params={}, SerializerClass=None):
        params = {k: v for k, v in query_params.items()}
        parent_level = int(params.pop('parent_level', 0))
        parent_id = params.pop('parent_id', None)

        if not parent_level and parent_id is None:
            return super()._filter(lookup_args,
                                   query_params=query_params,
                                   SerializerClass=SerializerClass)

        casestudy = lookup_args['casestudy_pk']
        level_pk = int(lookup_args['level_pk'])
        own_level = AdminLevels.objects.get(pk=level_pk)
        if not parent_level:
            try:
                parent_level = Area.objects.get(pk=parent_id).adminlevel.level
            except Area.DoesNotExist:
                raise exceptions.NotFound()
        levels = AdminLevels.objects.filter(casestudy__id=casestudy,
                                            level__gt=parent_level,
                                            level__lte=own_level.level)
        level_ids = [l.level for l in levels]

        try:
            parents = [Areas.by_level[parent_level].objects.get(pk=parent_id)]
        except ObjectDoesNotExist as e:
            raise exceptions.NotFound(e)
        #queryset = self.get_queryset()
        for level_id in level_ids:
            model = Areas.by_level[level_id]
            areas = model.objects.filter(parent_area__in=parents)
            parents.extend(areas)
        filter_args = self.get_filter_args(queryset=areas,
                                           query_params=params)
        queryset = areas.filter(**filter_args)
        queryset = queryset.annotate(pnt=PointOnSurface('geom'))
        return queryset

    def get_queryset(self):
        model = self.serializer_class.Meta.model
        casestudy_pk = self.kwargs.get('casestudy_pk')
        areas = model.objects.select_related("adminlevel").filter(
            adminlevel__casestudy=casestudy_pk)
        areas = areas.annotate(pnt=PointOnSurface('geom'))
        return areas

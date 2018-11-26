from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from django.utils.translation import ugettext as _
from django.contrib.gis.geos import Polygon, MultiPolygon

from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from rest_framework_gis.serializers import (GeoFeatureModelSerializer,
                                            GeometryField)

from repair.apps.studyarea.models import (AdminLevels,
                                          Area,
                                          )

from repair.apps.login.serializers import (InCasestudyField,
                                           InCasestudyListField,
                                           CreateWithUserInCasestudyMixin,
                                           ForceMultiMixin,
                                           CasestudyField,
                                           )


class AreaListField(InCasestudyListField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'casestudy__id',
        'level_pk': 'id',
    }


class AdminLevelSerializer(CreateWithUserInCasestudyMixin,
                           NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    area_set = AreaListField(view_name='area-list')

    class Meta:
        model = AdminLevels
        fields = ('url', 'id', 'casestudy', 'name',
                  'level',
                  'area_set',
                  )


class AdminLevelField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}


class AreaSerializer(CreateWithUserInCasestudyMixin,
                     NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'adminlevel__casestudy__id',
                            'level_pk': 'adminlevel__id', }
    casestudy = CasestudyField(source='adminlevel.casestudy',
                               view_name='casestudy-detail')
    point_on_surface = GeometryField(source='pnt', read_only=True)
    geometry = GeometryField(source='geom')

    class Meta:
        model = Area
        fields = ('url', 'id',
                  'casestudy',
                  'name', 'code',
                  'point_on_surface',
                  'geometry'
                  )


class AreaGeoJsonSerializer(ForceMultiMixin,
                            GeoFeatureModelSerializer,
                            AreaSerializer):
    """
    Detail serializer for Areas adding the geom field
    and returning a geojson
    """
    adminlevel = AdminLevelField(view_name='adminlevels-detail')
    parent_area = serializers.IntegerField(
        required=False,
        allow_null=True,
        source='parent_area.id')
    parent_area_code = serializers.StringRelatedField(
        required=False,
        allow_null=True,
        source='parent_area.code')
    parent_level = serializers.IntegerField(read_only=True,
                                            required=False,
                                            allow_null=True,
                                            source='parent_area.adminlevel.id')
    geometry = GeometryField(source='geom')

    class Meta(AreaSerializer.Meta):
        geo_field = 'geometry'
        fields = ('url', 'id', 'casestudy', 'name', 'code',
                  'adminlevel',
                  'parent_area',
                  'parent_level',
                  'parent_area_code',
                  'point_on_surface'
                  )

    def update(self, instance, validated_data):
        """cast geomfield to multipolygon"""
        self.convert2multi(validated_data, 'geom')
        return super().update(instance, validated_data)

    def create(self, validated_data):
        """Create a new areas"""
        adminlevel = self.get_level(validated_data=validated_data)

        if 'features' not in validated_data:
            parent_area_id = validated_data.pop('parent_area', None)
            # ignore code here
            parent_code = validated_data.pop('parent_area_code', None)
            if (parent_area_id):
                validated_data['parent_area'] = \
                    Area.objects.get(**parent_area_id)
            if isinstance(validated_data['geom'], Polygon):
                validated_data['geom'] = MultiPolygon(validated_data['geom'])
            obj = self.Meta.model.objects.create(
                adminlevel=adminlevel,
                **validated_data)
            return obj

        parent_level_pk = validated_data.pop('parent_level', None)
        if parent_level_pk is not None:
            parent_adminlevel = AdminLevels.objects.get(level=parent_level_pk)

        for feature in validated_data['features']:
            parent_area_id = feature.pop('parent_area', None)
            parent_area_code = feature.pop('parent_area_code', None)
            if (parent_area_id is not None) and (parent_area_code is not None):
                raise serializers.ValidationError(_(
                    "you may only pass parent_area_id OR "
                    "parent_area_code (not both)"))
            self.convert2multi(feature, 'geom')
            obj = Area.objects.create(
                adminlevel=adminlevel,
                **feature)
            parent_area = None
            if parent_area_id:
                parent_area = Area.objects.get(**parent_area_id)
                obj.parent_area = parent_area
            if parent_area_code:
                if not parent_level_pk:
                    raise serializers.ValidationError(_(
                        "parent_level is required when relating to "
                        "parents by code"))
                parent_area = Area.objects.get(
                    adminlevel=parent_adminlevel,
                    code=parent_area_code)
            if parent_area:
                obj.parent_area = parent_area
            obj.save()
        return obj

    def get_level(self, validated_data=None):
        validated_data = validated_data or {}
        url_pks = self.context['request'].session['url_pks']
        level_pk = validated_data.pop('level',
                                      url_pks['level_pk'])
        adminlevel = AdminLevels.objects.get(pk=level_pk)
        return adminlevel


class AreaGeoJsonPostSerializer(AreaGeoJsonSerializer):

    class Meta(AreaGeoJsonSerializer.Meta):
        fields = ('url', 'id', 'name', 'code',
                  'parent_level', 'parent_area',
                  'parent_area_code')

    def to_internal_value(self, data):
        """
        Override the parent method to parse all features and
        remove the GeoJSON formatting
        """
        data = data.copy()
        parent_level = data.pop('parent_level', None)

        if data.get('type') == 'FeatureCollection':
            internal_data_list = list()
            for feature in data.get('features', []):
                if 'properties' in feature:
                    feature = self.unformat_geojson(feature)
                internal_data = super().to_internal_value(feature)
                internal_data['parent_area_code'] = \
                    feature.get('parent_area_code')
                internal_data_list.append(internal_data)

            return {'features': internal_data_list,
                    'parent_level': parent_level,
                    }
        return super().to_internal_value(data)

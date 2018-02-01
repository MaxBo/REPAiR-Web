from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from rest_framework_gis.serializers import (GeoFeatureModelSerializer,
                                            GeometryField)

from repair.apps.studyarea.models import (AdminLevels,
                                          Area,
                                          Areas
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


class ParentAreaField(serializers.IntegerField):
    def to_representation(self, value):
        concrete_area = self.get_concrete_area()
        return str(concrete_area.parent_area_id)

    def get_concrete_area(self):
        obj = self.root.instance
        level = obj.adminlevel.level
        area_class = Areas.by_level[level]
        concrete_area = area_class.objects.get(pk=obj.pk)
        return concrete_area

    def get_attribute(self, instance):
        """get the attribute"""
        return super().get_attribute(self.get_concrete_area())


class ParentAreaLevel(ParentAreaField):
    def to_representation(self, value):
        concrete_area = self.get_concrete_area()
        return str(concrete_area.parent_area.adminlevel_id)

    def get_attribute(self, instance):
        """get the level attribute"""
        concrete_area = super().get_attribute(self.get_concrete_area())
        if concrete_area is None:
            return None
        else:
            return concrete_area.adminlevel


class AreaSerializer(CreateWithUserInCasestudyMixin,
                     NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'adminlevel__casestudy__id',
                            'level_pk': 'adminlevel__id', }
    casestudy = CasestudyField(source='adminlevel.casestudy',
                               view_name='casestudy-detail')

    class Meta:
        model = Area
        fields = ('url', 'id',
                  'casestudy',
                  'name', 'code',
                  )


class AreaGeoJsonSerializer(ForceMultiMixin,
                            GeoFeatureModelSerializer,
                            AreaSerializer):
    """
    Detail serializer for Areas adding the geom field
    and returning a geojson
    """
    adminlevel = AdminLevelField(view_name='adminlevels-detail')

    geometry = GeometryField(source='geom')
    parent_area = ParentAreaField(read_only=True, allow_null=True)
    parent_level = ParentAreaLevel(read_only=True,
                                   allow_null=True,
                                   source='parent_area')

    class Meta(AreaSerializer.Meta):
        geo_field = 'geometry'
        fields = ('url', 'id', 'casestudy', 'name', 'code',
                  'adminlevel',
                  'parent_area',
                  'parent_level',
                  )

    def update(self, instance, validated_data):
        """cast geomfield to multipolygon"""
        self.convert2multi(validated_data, 'geom')
        return super().update(instance, validated_data)

    def create(self, validated_data):
        """Create a new user and its profile"""
        adminlevel = self.get_level(validated_data=validated_data)

        if 'features' not in validated_data:
            obj = self.Meta.model.objects.create(
                adminlevel=adminlevel,
                **validated_data)
            return obj

        parent_level_pk = validated_data.pop('parent_level')
        if parent_level_pk is not None:
            parent_adminlevel = AdminLevels.objects.get(level=parent_level_pk)

            parent_area_class = Areas.by_level.get(parent_adminlevel.level)
        else:
            parent_area_class = None

        for feature in validated_data['features']:
            parent_area_code = feature.pop('parent_area', None)
            self.convert2multi(feature, 'geom')
            model = Areas.by_level[adminlevel.level]
            obj = model.objects.create(
                adminlevel=adminlevel,
                **feature)
            if parent_area_class is not None:
                try:
                    parent_area = parent_area_class.objects.get(
                        adminlevel=parent_adminlevel,
                        code=parent_area_code)
                    obj.parent_area = parent_area
                except ObjectDoesNotExist:
                    pass
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
    parent_level = serializers.IntegerField(write_only=True, required=False)
    parent_area = serializers.CharField(write_only=True, required=False)

    class Meta(AreaGeoJsonSerializer.Meta):
        fields = ('url', 'id', 'name', 'code',
                  'parent_level', 'parent_area')

    def to_internal_value(self, data):
        """
        Override the parent method to parse all features and
        remove the GeoJSON formatting
        """
        parent_level = data.pop('parent_level', None)

        if data.get('type') == 'FeatureCollection':
            internal_data_list = list()
            for feature in data.get('features', []):
                if 'properties' in feature:
                    feature = self.unformat_geojson(feature)
                internal_data = super().to_internal_value(feature)
                internal_data_list.append(internal_data)

            return {'features': internal_data_list,
                    'parent_level': parent_level,
                    }
        return super().to_internal_value(data)

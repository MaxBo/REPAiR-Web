from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from rest_framework_gis.serializers import GeoFeatureModelSerializer, GeometryField

from repair.apps.studyarea.models import (StakeholderCategory,
                                          Stakeholder,
                                          AdminLevels,
                                          Area,
                                          )
from repair.apps.login.models import CaseStudy
from repair.apps.login.serializers import (CaseStudySerializer,
                                           InCasestudyField,
                                           InCaseStudyIdentityField,
                                           InCasestudyListField,
                                           IdentityFieldMixin,
                                           CreateWithUserInCasestudyMixin,
                                           ForceMultiMixin,
                                           )

import repair.apps.studyarea.models as smodels

AreaSubModels = {m._level: m for m in smodels.__dict__.values()
                 if isinstance(m, type) and issubclass(m, Area)
                 and not m == Area
                 }


class StakeholderCategoryField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}


class StakeholderSetField(InCasestudyField):
    lookup_url_kwarg = 'stakeholdercategory_pk'
    parent_lookup_kwargs = {
        'casestudy_pk': 'stakeholder_category__casestudy__id',
        'stakeholdercategory_pk': 'stakeholder_category__id', }


class StakeholderListField(IdentityFieldMixin, StakeholderSetField):
    """"""
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id',
                            'stakeholdercategory_pk': 'id', }


class StakeholderSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'stakeholder_category__casestudy__id',
        'stakeholdercategory_pk': 'stakeholder_category__id',
    }
    stakeholder_category = StakeholderCategoryField(
        view_name='stakeholdercategory-detail'
    )

    class Meta:
        model = Stakeholder
        fields = ('url', 'id', 'name', 'stakeholder_category')


class StakeholderSetSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'stakeholder_category__casestudy__id',
        'stakeholdercategory_pk': 'stakeholder_category__id',
    }
    class Meta:
        model = Stakeholder
        fields = ('url', 'id', 'name')


class StakeholderCategorySerializer(CreateWithUserInCasestudyMixin,
                                    NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    stakeholder_list = StakeholderListField(source='stakeholder_set',
                                            view_name='stakeholder-list')
    stakeholder_set = StakeholderSetField(many=True,
                                          view_name='stakeholder-detail',
                                          read_only=True)

    class Meta:
        model = StakeholderCategory
        fields = ('url', 'id', 'name', 'stakeholder_set', 'stakeholder_list',
                  )

    def get_required_fields(self, user, kic=None):
        required_fields = {'casestudy': user.casestudy,}
        return required_fields


class AreaListField(InCasestudyListField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'casestudy__id',
        'level_pk': 'id',
    }
    #class Meta:
        #model = Stakeholder
        #fields = ('url', 'id', 'name')


class AdminLevelSerializer(CreateWithUserInCasestudyMixin,
                           NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    area_set = AreaListField(view_name='area-list')

    class Meta:
        model = AdminLevels
        fields = ('url', 'id', 'casestudy', 'name', 'level',
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
        level = obj.level.level
        area_class = AreaSubModels[level]
        concrete_area = area_class.objects.get(pk=obj.pk)
        return concrete_area

class ParentAreaLevel(ParentAreaField):
    def to_representation(self, value):
        concrete_area = self.get_concrete_area()
        return str(concrete_area.parent_area.level_id)


class AreaSerializer(CreateWithUserInCasestudyMixin,
                     NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id',
                            'level_pk': 'level__id',}

    level = AdminLevelField(view_name='adminlevels-detail')

    class Meta:
        model = Area
        fields = ('url', 'id', 'casestudy', 'name', 'code',
                  'level',
                  )


class AreaGeoJsonSerializer(ForceMultiMixin,
                            GeoFeatureModelSerializer,
                            AreaSerializer):
    """
    Detail serializer for Areas adding the geom field
    and returning a geojson
    """
    geometry = GeometryField(source='geom')
    parent_area = ParentAreaField(read_only=True, allow_null=True)
    parent_level = ParentAreaLevel(read_only=True, allow_null=True)

    class Meta(AreaSerializer.Meta):
        geo_field = 'geometry'
        fields = ('url', 'id', 'casestudy', 'name', 'code',
                      'level',
                      'parent_area',
                      'parent_level',
                      )

    def update(self, instance, validated_data):
        """cast geomfield to multipolygon"""
        self.convert2multi(validated_data, 'geom')
        return super().update(instance, validated_data)

    def create(self, validated_data):
        """Create a new user and its profile"""
        casestudy, level = self.get_casestudy_level(
            validated_data=validated_data)

        if not 'features' in validated_data:
            obj = self.Meta.model.objects.create(
                casestudy=casestudy,
                level=level,
                **validated_data)
            return obj

        parent_level_pk = validated_data.pop('parent_level')
        if parent_level_pk is not None:
            parent_level = AdminLevels.objects.get(level=parent_level_pk)

            parent_area_class = AreaSubModels.get(parent_level.level)
        else:
            parent_area_class = None

        for feature in validated_data['features']:
            parent_area_code = feature.pop('parent_area', None)
            self.convert2multi(feature, 'geom')
            model = AreaSubModels[level.level]
            obj = model.objects.create(
                casestudy=casestudy,
                **feature)
            if parent_area_class is not None:
                parent_area = parent_area_class.objects.get(casestudy=casestudy,
                                                            code=parent_area_code)
                obj.parent_area=parent_area
                obj.save()

        return obj

    def get_casestudy_level(self, validated_data=None):
        validated_data = validated_data or {}
        url_pks = self.context['request'].session['url_pks']
        casestudy_pk = validated_data.pop('casestudy_id',
                                          url_pks['casestudy_pk'])
        level_pk = validated_data.pop('level',
                                      url_pks['level_pk'])
        casestudy = CaseStudy.objects.get(pk=casestudy_pk)
        level = AdminLevels.objects.get(pk=level_pk)
        return casestudy, level

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
        casestudy, level = self.get_casestudy_level()
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
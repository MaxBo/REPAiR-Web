from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _
from repair.apps.login.models import CaseStudy, User
from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           InCasestudySerializerMixin,
                                           InCasestudyField,
                                           InCasestudyListField,
                                           IdentityFieldMixin,
                                           NestedHyperlinkedRelatedField,
                                           NestedHyperlinkedRelatedField2,
                                           IDRelatedField,
                                           CreateWithUserInCasestudyMixin,
                                           UserInCasestudyField)
from rest_framework.serializers import HyperlinkedModelSerializer
from repair.apps.statusquo.models import (Aim,
                                          ImpactCategory,
                                          ImpactCategoryInSustainability,
                                          SustainabilityField,
                                          TargetSpatialReference,
                                          TargetValue,
                                          IndicatorCharacterisation,
                                          FlowTarget)


class ImpactCategorySerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    name = serializers.CharField()
    area_of_protection = IDRelatedField()
    spatial_differentiation = serializers.BooleanField()

    class Meta:
        model = ImpactCategory
        fields = ('url',
                  'id',
                  'name',
                  'area_of_protection',
                  'spatial_differentiation')


class ImpactCategoryInSustainabilitySerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'sustainability_pk': 'sustainability_field__id'}
    impact_category = IDRelatedField()

    class Meta:
        model = ImpactCategory
        fields = ('url',
                  'id',
                  'impact_category')


class SustainabilityFieldSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    name = serializers.CharField()

    class Meta:
        model = SustainabilityField
        fields = ('url',
                  'id',
                  'name')


class TargetValueSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    text = serializers.CharField()
    number = serializers.FloatField()
    factor = serializers.FloatField()

    class Meta:
        model = TargetValue
        fields = ('url',
                  'id',
                  'text',
                  'number',
                  'factor')


class TargetSpatialReferenceSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    name = serializers.CharField()
    text = serializers.CharField()

    class Meta:
        model = TargetSpatialReference
        fields = ('url',
                  'id',
                  'name',
                  'text')


class IndicatorCharacterisationSerializer(NestedHyperlinkedModelSerializer):
    name = serializers.CharField()

    class Meta:
        model = IndicatorCharacterisation
        fields = ('url',
                  'id',
                  'name')


class FlowTargetSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'userobjective__aim__casestudy__id',
                            'userobjective_pk': 'userobjective__id'}
    indicator = IDRelatedField()
    target_value = IDRelatedField()
    user = IDRelatedField(source='userobjective.user.id',
                          allow_null=True, read_only=True)
    keyflow = IDRelatedField(source='userobjective.aim.keyflow.id',
                             allow_null=True, read_only=True)

    class Meta:
        model = FlowTarget
        fields = ('id',
                  'indicator',
                  'target_value',
                  'user',
                  'keyflow',
                  'notes')

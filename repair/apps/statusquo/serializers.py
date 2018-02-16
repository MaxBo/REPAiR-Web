from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _
from repair.apps.login.models import CaseStudy, User
from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           InCasestudySerializerMixin,
                                           InCasestudyField,
                                           InCasestudyListField,
                                           IdentityFieldMixin,
                                           NestedHyperlinkedRelatedField,
                                           IDRelatedField)
from repair.apps.statusquo.models import (Aim,
                                          Challenge,
                                          IndicatorAreaOfProtection,
                                          IndicatorImpactCategory,
                                          IndicatorSustainabilityField,
                                          Target,
                                          TargetSpatialReference,
                                          TargetValue)


class AimSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    casestudy = IDRelatedField()
    text = serializers.CharField()

    class Meta:
        model = Aim
        fields = ('url',
                  'id',
                  'casestudy',
                  'text')


class ChallengeSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    casestudy = IDRelatedField()
    text = serializers.CharField()

    class Meta:
        model = Challenge
        fields = ('url',
                  'id',
                  'casestudy',
                  'text')

class IndicatorAreaOfProtectionSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    name = serializers.CharField()
    sustainability_field = IDRelatedField()

    class Meta:
        model = IndicatorAreaOfProtection
        fields = ('url',
                  'id',
                  'name',
                  'sustainability_field')


class IndicatorImpactCategorySerielizer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    name = serializers.CharField()
    area_of_protection = IDRelatedField()
    spatial_differentiation = serializers.BooleanField()

    class Meta:
        model = IndicatorImpactCategory
        fields = ('url',
                  'id',
                  'name',
                  'area_of_protection',
                  'spatial_differentiation')


class IndicatorSustainabilityFieldSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    name = serializers.CharField()

    class Meta:
        model = IndicatorSustainabilityField
        fields = ('url',
                  'id',
                  'name')


class TargetSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    casestudy = IDRelatedField()
    user = IDRelatedField()
    aim = IDRelatedField()
    impact_category = IDRelatedField()
    target_value = IDRelatedField()
    spatial_reference = IDRelatedField()

    class Meta:
        model = Target
        fields = ('url',
                  'id',
                  'casestudy',
                  'user',
                  'aim',
                  'impact_category',
                  'target_value',
                  'spatial_reference')


class TargetValueSerializer(NestedHyperlinkedModelSerializer):
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





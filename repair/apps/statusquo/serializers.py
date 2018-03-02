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
from repair.apps.statusquo.models import (Aim,
                                          Challenge,
                                          AreaOfProtection,
                                          ImpactCategory,
                                          ImpactCategoryInSustainability,
                                          SustainabilityField,
                                          Target,
                                          TargetSpatialReference,
                                          TargetValue,
                                          IndicatorCharacterisation)
from rest_framework.serializers import HyperlinkedModelSerializer


class AimSerializer(InCasestudySerializerMixin,
                    NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    casestudy = IDRelatedField()
    text = serializers.CharField()

    class Meta:
        model = Aim
        fields = ('url',
                  'id',
                  'text',
                  'casestudy')


class AimPostSerializer(InCasestudySerializerMixin,
                        NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    text = serializers.CharField()

    class Meta:
        model = Aim
        fields = ('url',
                  'id',
                  'text')


class ChallengeSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    text = serializers.CharField()

    class Meta:
        model = Challenge
        fields = ('url',
                  'id',
                  'text')


class ChallengePostSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    casestudy = IDRelatedField()
    text = serializers.CharField()

    class Meta:
        model = Challenge
        fields = ('url',
                  'id',
                  'casestudy',
                  'text')

class AreaOfProtectionSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'sustainability_pk': 'sustainability_field__id'}
    name = serializers.CharField()
    sustainability_field = IDRelatedField()

    class Meta:
        model = AreaOfProtection
        fields = ('url',
                  'id',
                  'name',
                  'sustainability_field')


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


class TargetSerializer(CreateWithUserInCasestudyMixin,
                       NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'user_pk': 'user__id',}
    aim = IDRelatedField()
    impact_category = IDRelatedField()
    target_value = IDRelatedField()
    spatial_reference = IDRelatedField()
    user = UserInCasestudyField(
        view_name='userincasestudy-detail')

    class Meta:
        model = Target
        fields = ('url',
                  'id',
                  'aim',
                  'impact_category',
                  'target_value',
                  'spatial_reference',
                  'user')


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






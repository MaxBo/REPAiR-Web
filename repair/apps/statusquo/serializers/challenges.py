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
from repair.apps.statusquo.models import Challenge


class ChallengeSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    casestudy = IDRelatedField()
    text = serializers.CharField()

    class Meta:
        model = Challenge
        fields = ('url',
                  'id',
                  'casestudy',
                  'text',
                  'priority')


class ChallengePostSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    text = serializers.CharField()

    class Meta:
        model = Challenge
        fields = ('url',
                  'id',
                  'text',
                  'priority')
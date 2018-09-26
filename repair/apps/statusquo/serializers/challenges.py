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
    keyflow = IDRelatedField(allow_null=True)
    text = serializers.CharField()

    class Meta:
        model = Challenge
        fields = ('url',
                  'id',
                  'casestudy',
                  'keyflow',
                  'text',
                  'priority')


class ChallengePostSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    text = serializers.CharField()
    keyflow = IDRelatedField(allow_null=True, required=False)

    class Meta:
        model = Challenge
        fields = ('url',
                  'id',
                  'text',
                  'keyflow',
                  'priority')

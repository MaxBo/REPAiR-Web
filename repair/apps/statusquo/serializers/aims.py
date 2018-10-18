from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _
from repair.apps.login.models import CaseStudy, User
from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           InCasestudySerializerMixin,
                                           IdentityFieldMixin,
                                           NestedHyperlinkedRelatedField,
                                           NestedHyperlinkedRelatedField2,
                                           IDRelatedField,
                                           CreateWithUserInCasestudyMixin,
                                           UserInCasestudyField)
from rest_framework.serializers import HyperlinkedModelSerializer
from repair.apps.statusquo.models import (Aim, UserObjective,
                                          AreaOfProtection, FlowTarget)


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


class AimSerializer(InCasestudySerializerMixin,
                    NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    casestudy = IDRelatedField()
    keyflow = IDRelatedField(allow_null=True)
    text = serializers.CharField()

    class Meta:
        model = Aim
        fields = ('url',
                  'id',
                  'text',
                  'casestudy',
                  'keyflow',
                  'priority',
                  'description')


class AimPostSerializer(InCasestudySerializerMixin,
                        NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    text = serializers.CharField()
    keyflow = IDRelatedField(allow_null=True, required=False)

    class Meta:
        model = Aim
        fields = ('url',
                  'id',
                  'keyflow',
                  'text',
                  'priority',
                  'description')


class UserObjectiveSerializer(InCasestudySerializerMixin,
                              serializers.ModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'aim__casestudy__id'}
    aim = IDRelatedField()
    user = IDRelatedField()
    keyflow = serializers.IntegerField(source='aim.keyflow.id',
                                       allow_null=True, read_only=True)
    #flow_targets = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = UserObjective
        extra_kwargs = {'target_areas': {'required': False,
                                         'allow_empty': True}}
        fields = ('id',
                  'aim',
                  'user',
                  'priority',
                  'keyflow',
                  'target_areas',
                  #'flow_targets'
                  )

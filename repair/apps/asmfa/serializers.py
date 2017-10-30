from rest_framework import serializers

from repair.apps.asmfa.models import (ActivityGroup, Activity, Actor, Flow,
                                      Actor2Actor, Activity2Activity,
                                      Group2Group)


class ActivityGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityGroup
        fields = ('code', 'name')


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ('id', 'nace', 'name', 'own_activitygroup')


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ('BvDid', 'name', 'consCode', 'year', 'revenue',
                  'employees', 'BvDii', 'website', 'own_activity')


class ActorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ('BvDid', 'name', 'own_activity')


class FlowSerializer(serializers.ModelSerializer):
    """Abstract Base Class for a Flow Serializer"""
    class Meta:
        model = Flow
        fields = ('id', 'material', 'amount', 'quality', 'origin',
                  'destination', 'casestudy')


class Actor2ActorSerializer(FlowSerializer):
    class Meta(FlowSerializer.Meta):
        model = Actor2Actor


class Activity2ActivitySerializer(FlowSerializer):
    class Meta(FlowSerializer.Meta):
        model = Activity2Activity


class Group2GroupSerializer(FlowSerializer):
    class Meta(FlowSerializer.Meta):
        model = Group2Group

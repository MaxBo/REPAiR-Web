from repair.apps.asmfa.models import ActivityGroup, Activity, Actor, Flow

from rest_framework import serializers


class ActivityGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityGroup
        fields = ('code', 'name')


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ('id', 'nace', 'name')


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ('BvDid', 'name', 'consCode', 'year', 'revenue',
                  'employees', 'BvDii', 'website')


class FlowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flow
        fields = ('material', 'amount', 'quality', 'origin', 'destination')
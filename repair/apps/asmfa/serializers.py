from repair.apps.asmfa.models import (ActivityGroup, Activity, Actor, Flow,
                                      Actor2Actor, Activity2Activity,
                                      Group2Group)


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
        model = None
        fields = ('material', 'amount', 'quality', 'origin', 'destination',
                  'case_study')


class Actor2ActorSerializer(FlowSerializer):
    class Meta(FlowSerializer.Meta):
        model = Actor2Actor


class Activity2ActivitySerializer(FlowSerializer):
    class Meta(FlowSerializer.Meta):
        model = Activity2Activity


class Group2GroupSerializer(FlowSerializer):
    class Meta(FlowSerializer.Meta):
        model = Group2Group
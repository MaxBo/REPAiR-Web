from repair.apps.asmfa.models import ActivityGroup

from rest_framework import serializers


class ActivityGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityGroup
        fields = ('code', 'name')

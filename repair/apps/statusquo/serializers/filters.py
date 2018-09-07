from rest_framework import serializers
from repair.apps.statusquo.models import (FlowType, NodeLevel, Direction,
                                          FlowFilter)

from repair.apps.utils.serializers import EnumField
from repair.apps.login.serializers import IDRelatedField


class FlowFilterSerializer(serializers.ModelSerializer):
    flow_type = EnumField(enum=FlowType)
    filter_level = EnumField(enum=NodeLevel)
    direction = EnumField(enum=Direction)
    material = IDRelatedField(allow_null=True, required=False)

    class Meta:
        model = FlowFilter
        fields = ('name',
                  'description',
                  'keyflow',
                  'direction',
                  'material',
                  'flow_type',
                  'filter_level',
                  'node_ids')

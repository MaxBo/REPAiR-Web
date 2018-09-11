from rest_framework import serializers
from repair.apps.statusquo.models import (FlowType, NodeLevel, Direction,
                                          FlowFilter)

from repair.apps.utils.serializers import EnumField
from repair.apps.login.serializers import (IDRelatedField,
                                           NestedHyperlinkedModelSerializer)


class FlowFilterSerializer(serializers.ModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }
    flow_type = EnumField(enum=FlowType, required=False)
    filter_level = EnumField(enum=NodeLevel, required=False)
    direction = EnumField(enum=Direction, required=False)
    material = IDRelatedField(allow_null=True, required=False)

    class Meta:
        model = FlowFilter
        fields = ('id',
                  'name',
                  'description',
                  'direction',
                  'material',
                  'aggregate_materials',
                  'area_level',
                  'areas',
                  'flow_type',
                  'filter_level',
                  'node_ids')

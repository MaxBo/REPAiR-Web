
from repair.apps.asmfa.models import (Flow,
                                      Actor2Actor,
                                      Activity2Activity,
                                      Group2Group,
                                      )

from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           IDRelatedField)

from .keyflows import (KeyflowInCasestudyField,
                       KeyflowInCasestudyDetailCreateMixin)

from .nodes import (ActivityGroupField,
                    ActivityField,
                    ActorField)


class FlowSerializer(KeyflowInCasestudyDetailCreateMixin,
                     NestedHyperlinkedModelSerializer):
    """Abstract Base Class for a Flow Serializer"""
    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }
    keyflow = KeyflowInCasestudyField(view_name='keyflowincasestudy-detail',
                                      read_only=True)
    publication = IDRelatedField()

    class Meta:
        model = Flow
        fields = ('url', 'id',
                  'keyflow',
                  'amount', 'origin',
                  'destination', 'product', 'description', 'year')


class Group2GroupSerializer(FlowSerializer):
    origin = IDRelatedField()
    origin_url = ActivityGroupField(view_name='activitygroup-detail',
                                    source='origin',
                                    read_only=True)
    product = IDRelatedField()
    destination = IDRelatedField()
    destination_url = ActivityGroupField(view_name='activitygroup-detail',
                                         source='destination',
                                         read_only=True)

    class Meta(FlowSerializer.Meta):
        model = Group2Group
        fields = ('id', 'amount', 'keyflow', 'origin', 'origin_url',
                  'destination', 'destination_url', 'product', 'description',
                  'year', 'publication', )


class Activity2ActivitySerializer(FlowSerializer):
    origin = IDRelatedField()
    origin_url = ActivityField(view_name='activity-detail',
                               source='origin',
                               read_only=True)
    product = IDRelatedField()
    destination = IDRelatedField()
    destination_url = ActivityField(view_name='activity-detail',
                                    source='destination',
                                    read_only=True)

    class Meta(FlowSerializer.Meta):
        model = Activity2Activity
        fields = ('id', 'amount', 'keyflow', 'origin', 'origin_url',
                  'destination', 'destination_url', 'product', 'description',
                  'year', 'publication')


class Actor2ActorSerializer(FlowSerializer):
    origin = IDRelatedField()
    origin_url = ActorField(view_name='actor-detail',
                            source='origin',
                            read_only=True)
    product = IDRelatedField()
    destination = IDRelatedField()
    destination_url = ActorField(view_name='actor-detail',
                                 source='destination',
                                 read_only=True)

    class Meta(FlowSerializer.Meta):
        model = Actor2Actor
        fields = ('id', 'amount', 'keyflow',
                  'origin', 'origin_url',
                  'destination', 'destination_url', 'product', 'description',
                  'year', 'publication')

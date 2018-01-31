
from django.core.exceptions import ObjectDoesNotExist
from repair.apps.asmfa.models import (Flow,
                                      Actor2Actor,
                                      Activity2Activity,
                                      Group2Group,
                                      Composition
                                      )

from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           IDRelatedField)

from repair.apps.asmfa.serializers.keyflows import (
    KeyflowInCasestudyField, KeyflowInCasestudyDetailCreateMixin,
    ProductFractionSerializer, CompositionSerializer)

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
    publication = IDRelatedField(allow_null=True, required=False)
    composition = CompositionSerializer()

    class Meta:
        model = Flow
        fields = ('id', 'amount', 'keyflow', 'origin', 'origin_url',
                  'destination', 'destination_url', 'composition', 'description',
                  'year', 'publication', 'waste')
    
    def create(self, validated_data):
        comp_data = validated_data.pop('composition')
        instance = super().create(validated_data)
        validated_data['composition'] = comp_data
        return self.update(instance, validated_data)
    
    def update(self, instance, validated_data):
        comp_data = validated_data.pop('composition')
        comp_id = comp_data.get('id')
        
        # custom composition: no product or waste
        if comp_id is None or comp_id == instance.composition_id:
            # no former compostition
            if instance.composition is None:
                composition = Composition.objects.create()
            # former compostition
            else:
                composition = instance.composition

            if composition.is_custom:
                # update the fractions using the CompositionSerializer
                comp_data['id'] = composition.id
                composition = CompositionSerializer().update(
                    composition, comp_data)

        # product or waste
        else:
            # take the product or waste-instance as composition 
            composition = Composition.objects.get(id=comp_id)
            
            # if old composition is a custom composition, delete it
            if instance.composition is not None:
                old_composition = instance.composition
                if old_composition.is_custom:
                    old_composition.delete()
            
        # assign the composition to the flow
        instance.composition = composition
        return super().update(instance, validated_data)


class Group2GroupSerializer(FlowSerializer):
    origin = IDRelatedField()
    origin_url = ActivityGroupField(view_name='activitygroup-detail',
                                    source='origin',
                                    read_only=True)
    destination = IDRelatedField()
    destination_url = ActivityGroupField(view_name='activitygroup-detail',
                                         source='destination',
                                         read_only=True)

    class Meta(FlowSerializer.Meta):
        model = Group2Group
        fields = ('id', 'amount', 'keyflow', 'origin', 'origin_url',
                  'destination', 'destination_url', 'composition', 'description',
                  'year', 'publication', 'waste')


class Activity2ActivitySerializer(FlowSerializer):
    origin = IDRelatedField()
    origin_url = ActivityField(view_name='activity-detail',
                               source='origin',
                               read_only=True)
    destination = IDRelatedField()
    destination_url = ActivityField(view_name='activity-detail',
                                    source='destination',
                                    read_only=True)

    class Meta(FlowSerializer.Meta):
        model = Activity2Activity
        fields = ('id', 'amount', 'keyflow', 'origin', 'origin_url',
                  'destination', 'destination_url', 'composition', 'description',
                  'year', 'publication', 'waste')


class Actor2ActorSerializer(FlowSerializer):
    origin = IDRelatedField()
    origin_url = ActorField(view_name='actor-detail',
                            source='origin',
                            read_only=True)
    destination = IDRelatedField()
    destination_url = ActorField(view_name='actor-detail',
                                 source='destination',
                                 read_only=True)

    class Meta(FlowSerializer.Meta):
        model = Actor2Actor
        fields = ('id', 'amount', 'keyflow',
                  'origin', 'origin_url',
                  'destination', 'destination_url', 'composition', 'description',
                  'year', 'publication', 'waste')


from django.core.exceptions import ObjectDoesNotExist
from repair.apps.asmfa.models import (Flow,
                                      Actor2Actor,
                                      Activity2Activity,
                                      Group2Group,
                                      Composition,
                                      FractionFlow,
                                      ActorStock,
                                      GroupStock,
                                      ActivityStock,
                                      Stock
                                      )
from rest_framework import serializers

from repair.apps.asmfa.models import KeyflowInCasestudy

from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           IDRelatedField)

from repair.apps.asmfa.serializers.keyflows import (
    KeyflowInCasestudyField, KeyflowInCasestudyDetailCreateMixin,
    ProductFractionSerializer, CompositionSerializer)

from .nodes import (ActivityGroupField,
                    ActivityField,
                    ActorField)


class CompositionMixin:

    def create(self, validated_data):
        comp_data = validated_data.pop('composition')
        instance = super().create(validated_data)
        validated_data['composition'] = comp_data
        return self.update(instance, validated_data)

    def update(self, instance, validated_data):
        comp_data = validated_data.pop('composition', None)
        if comp_data:
            comp_id = comp_data.get('id')

            # custom composition: no product or waste
            if comp_id is None or comp_id == instance.composition_id:
                # no former compostition
                if instance.composition is None:
                    composition = Composition.objects.create()
                    if 'keyflow_id' in validated_data:
                        composition.keyflow = KeyflowInCasestudy.objects.get(
                            id=validated_data['keyflow_id'])
                    #composition.keyflow = self.request
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


class FlowSerializer(CompositionMixin,
                     NestedHyperlinkedModelSerializer):
    """Abstract Base Class for a Flow Serializer"""
    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }
    keyflow = KeyflowInCasestudyField(view_name='keyflowincasestudy-detail',
                                      read_only=True)
    publication = IDRelatedField(allow_null=True, required=False)
    process = IDRelatedField(allow_null=True)
    composition = CompositionSerializer()

    class Meta:
        model = Flow
        fields = ('id', 'amount', 'keyflow', 'origin', 'origin_url',
                  'destination', 'destination_url',
                  'origin_level', 'destination_level',
                  'composition', 'description',
                  'year', 'publication', 'waste', 'process')


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
                  'destination', 'destination_url',
                  'composition', 'description',
                  'year', 'publication', 'waste', 'process')


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
                  'destination', 'destination_url',
                  'composition', 'description',
                  'year', 'publication', 'waste', 'process')


class Actor2ActorSerializer(FlowSerializer):
    origin = IDRelatedField()
    #origin_url = ActorField(view_name='actor-detail',
                            #source='origin',
                            #read_only=True)
    destination = IDRelatedField()
    #destination_url = ActorField(view_name='actor-detail',
                                 #source='destination',
                                 #read_only=True)

    class Meta(FlowSerializer.Meta):
        model = Actor2Actor
        fields = ('id', 'amount', 'composition',
                  'origin',  'destination',
                  'description',
                  'year', 'publication', 'waste', 'process')


class FractionFlowSerializer(CompositionMixin,
                             NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }
    keyflow = IDRelatedField()
    publication = IDRelatedField(allow_null=True, required=False)
    process = IDRelatedField(allow_null=True)
    origin = IDRelatedField()
    destination = IDRelatedField()
    material = IDRelatedField()

    class Meta(FlowSerializer.Meta):
        model = FractionFlow
        fields = ('id', 'origin', 'destination', 'keyflow', 'material',
                  'amount', 'process', 'nace', 'waste', 'avoidable',
                  'hazardous', 'description', 'year', 'publication')



class StockSerializer(CompositionMixin,
                      NestedHyperlinkedModelSerializer):
    keyflow = KeyflowInCasestudyField(view_name='keyflowincasestudy-detail',
                                      read_only=True)
    composition = CompositionSerializer()
    publication = IDRelatedField(allow_null=True, required=False)

    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }

    class Meta:
        model = Stock
        fields = ('url', 'id', 'origin', 'amount',
                  'keyflow', 'year', 'composition',
                  'publication', 'waste'
                  )


class GroupStockSerializer(StockSerializer):
    origin = IDRelatedField()

    class Meta(StockSerializer.Meta):
        model = GroupStock


class ActivityStockSerializer(StockSerializer):
    origin = IDRelatedField()

    class Meta(StockSerializer.Meta):
        model = ActivityStock


class ActorStockSerializer(StockSerializer):
    origin = IDRelatedField()

    class Meta(StockSerializer.Meta):
        model = ActorStock

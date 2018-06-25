from rest_framework import serializers
from repair.apps.statusquo.models import (FlowIndicator, IndicatorFlow,
                                          KeyflowInCasestudy,
                                          IndicatorType, SpatialChoice,
                                          FlowType, NodeLevel)
from repair.apps.utils.serializers import EnumField


class IndicatorFlowSerializer(serializers.ModelSerializer):
    flow_type = EnumField(enum=FlowType)
    spatial_application = EnumField(enum=SpatialChoice)
    origin_node_level = EnumField(enum=NodeLevel)
    destination_node_level = EnumField(enum=NodeLevel)

    class Meta:
        model = IndicatorFlow
        fields = ('id',
                  'origin_node_level',
                  'origin_node_ids',
                  'destination_node_level',
                  'destination_node_ids',
                  'materials',
                  'spatial_application',
                  'flow_type')


class FlowIndicatorSerializer(serializers.ModelSerializer):
    flow_a = IndicatorFlowSerializer(allow_null=True, required=False)
    flow_b = IndicatorFlowSerializer(allow_null=True, required=False)
    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }
    indicator_type = EnumField(enum=IndicatorType, required=False)

    class Meta:
        model = FlowIndicator
        fields = ('id',
                  'name',
                  'unit',
                  'description',
                  'indicator_type',
                  'flow_a',
                  'flow_b')

    def create(self, validated_data):
        flow_a = validated_data.pop('flow_a', None)
        flow_b = validated_data.pop('flow_b', None)
        url_pks = self.context['request'].session['url_pks']
        keyflow_pk = url_pks.get('keyflow_pk')
        keyflow = KeyflowInCasestudy.objects.get(id=keyflow_pk)
        validated_data['keyflow'] = keyflow

        instance = self.Meta.model.objects.create(
            **validated_data)
        
        validated_data['flow_a'] = flow_a
        validated_data['flow_b'] = flow_b
        instance = self.update(instance, validated_data)
        return instance

    def update(self, instance, validated_data):
        
        for field in ['flow_a', 'flow_b']:
            val_flow = validated_data.pop(field, None)
            indicator_flow = getattr(instance, field)
            if val_flow is None:
                if indicator_flow is not None:
                    indicator_flow.delete()
                continue
            if indicator_flow is None:
                indicator_flow = IndicatorFlow()
                indicator_flow.save()
            for attr, value in val_flow.items():
                if attr == 'id':
                    continue
                if attr == 'materials':
                    getattr(indicator_flow, attr).set(value)
                    continue
                setattr(indicator_flow, attr, value)
            setattr(instance, field, indicator_flow)
            indicator_flow.save()
    
        # update other attributes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
        
        #"""update the user-attributes, including fraction information"""
        #composition = instance

        ## handle product fractions
        #new_fractions = validated_data.pop('fractions', None)

        #if new_fractions is not None:
            #product_fractions = ProductFraction.objects.filter(
                #composition=composition)
            ## delete existing rows not needed any more
            #ids = [fraction.get('id') for fraction in new_fractions if fraction.get('id') is not None]
            #to_delete = product_fractions.exclude(id__in=ids)
            #to_delete.delete()
            ## add or update new fractions
            #for new_fraction in new_fractions:
                #material_id = getattr(new_fraction.get('material'), 'id')
                #material = Material.objects.get(id=material_id)
                #fraction_id = new_fraction.get('id')
                ## create new fraction
                #if (fraction_id is None or
                    #len(product_fractions.filter(id=fraction_id)) == 0):
                    #fraction = ProductFraction(composition=composition)
                ## change existing fraction
                #else:
                    #fraction = product_fractions.get(id=fraction_id)

                #for attr, value in new_fraction.items():
                    #if attr in ('composition', 'id'):
                        #continue
                    #setattr(fraction, attr, value)
                #fraction.save()

        ## update other attributes
        #for attr, value in validated_data.items():
            #setattr(instance, attr, value)
        #instance.save()
        #return instance
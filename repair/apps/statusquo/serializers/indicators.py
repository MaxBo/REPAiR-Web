from rest_framework import serializers
from repair.apps.statusquo.models import FlowIndicator, IndicatorFlow


class IndicatorFlowSerializer(serializers.ModelSerializer):

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
    flow_a = IndicatorFlowSerializer(required=True)
    flow_b = IndicatorFlowSerializer(allow_null=True)
    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }

    class Meta:
        model = FlowIndicator
        fields = ('id',
                  'name',
                  'unit',
                  'description',
                  'indicator_type',
                  'flow_a',
                  'flow_b')

    #def create(self, validated_data):
        #fractions = validated_data.pop('fractions')
        #instance = super().create(validated_data)
        #validated_data['fractions'] = fractions
        #self.update(instance, validated_data)
        #return instance

    #def update(self, instance, validated_data):
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
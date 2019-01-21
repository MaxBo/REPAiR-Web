from rest_framework import serializers

from repair.apps.conclusions.models import Conclusion, ConsensusLevel, Section


class ConclusionSerializer(serializers.ModelSerializer):
    step_name = serializers.CharField(source='get_step_display', read_only=True)

    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id'
    }

    class Meta:
        model = Conclusion
        fields = ('id', 'step', 'step_name', 'text', 'link', 'image',
                  'consensus_level', 'section')
        extra_kwargs = {
            'text': {'required': False, 'allow_null': True,
                     'allow_blank': True},
            'link': {'required': False, 'allow_null': True,
                     'allow_blank': True},
            'image': {'required': False, 'allow_null': True},
        }


class ConsensusSerializer(serializers.ModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}

    class Meta:
        model = ConsensusLevel
        fields = ('id', 'name', 'priority')


class SectionSerializer(serializers.ModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}

    class Meta:
        model = Section
        fields = ('id', 'name', 'priority')

from rest_framework import serializers
from wand.image import Image
from django.core.files.base import File
import io
import os

from repair.apps.conclusions.models import (Conclusion, ConsensusLevel, Section,
                                            ConclusionReport)


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


class ConclusionReportSerializer(serializers.ModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}

    class Meta:
        model = ConclusionReport
        fields = ('id',
                  'name',
                  'report',
                  'thumbnail')


class ConclusionReportUpdateSerializer(serializers.ModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}

    class Meta:
        model = ConclusionReport
        fields = ('name', )


class ConclusionReportCreateSerializer(serializers.ModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}

    class Meta:
        model = ConclusionReport
        fields = ('name', 'report')

    def create(self, validated_data):
        instance = super().create(validated_data)
        instance.save()
        pdf = Image(filename=instance.report.file.name)
        image = Image(
            width=pdf.width,
            height=pdf.height
        )
        image.composite(pdf.sequence[0])
        blob = image.make_blob('png')
        with io.BytesIO(blob) as stream:
            file = File(stream)
            fn = f'{os.path.split(instance.report.name)[-1]}.thumbnail.png'
            instance.thumbnail.save(fn, file)
        return instance

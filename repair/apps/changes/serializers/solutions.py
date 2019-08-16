from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from django.contrib.gis.db.models.functions import MakeValid, GeoFunc
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from repair.apps.asmfa.models import Activity
from repair.apps.changes.models import (SolutionCategory,
                                        Solution,
                                        ImplementationQuestion,
                                        SolutionPart,
                                        AffectedFlow,
                                        PossibleImplementationArea,
                                        Scheme,
                                        FlowReference
                                        )

from repair.apps.login.serializers import (InCasestudyField,
                                           UserInCasestudyField,
                                           InCaseStudyIdentityField,
                                           IdentityFieldMixin,
                                           CreateWithUserInCasestudyMixin,
                                           IDRelatedField)
from repair.apps.statusquo.models import SpatialChoice
from repair.apps.utils.serializers import EnumField


class CollectionExtract(GeoFunc):
    function='ST_CollectionExtract'


class SolutionCategorySerializer(CreateWithUserInCasestudyMixin,
                                 NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }

    class Meta:
        model = SolutionCategory
        fields = ('url', 'id', 'name')
        read_only_fields = ('url', 'id')


class SolutionDetailCreateMixin:
    def create(self, validated_data):
        """Create a new solution quantity"""
        url_pks = self.context['request'].session['url_pks']
        solution_pk = url_pks['solution_pk']
        solution = Solution.objects.get(id=solution_pk)

        obj = self.Meta.model.objects.create(
            solution=solution,
            **validated_data)
        return obj


class ImplementationQuestionSerializer(SolutionDetailCreateMixin,
                                       NestedHyperlinkedModelSerializer):
    solution = IDRelatedField(read_only=True)
    parent_lookup_kwargs = {
        'casestudy_pk': 'solution__solution_category__keyflow__casestudy__id',
        'keyflow_pk': 'solution__solution_category__keyflow__id',
        'solution_pk': 'solution__id'
    }

    class Meta:
        model = ImplementationQuestion
        fields = ('url', 'id', 'solution', 'question', 'select_values',
                  'step', 'min_value', 'max_value', 'is_absolute')
        extra_kwargs = {'step': {'required': False},
                        'select_values': {'required': False}}


class PossibleImplementationAreaSerializer(SolutionDetailCreateMixin,
                                           NestedHyperlinkedModelSerializer):
    solution = IDRelatedField(read_only=True)
    edit_mask = serializers.ReadOnlyField()
    parent_lookup_kwargs = {
        'casestudy_pk': 'solution__solution_category__keyflow__casestudy__id',
        'keyflow_pk': 'solution__solution_category__keyflow__id',
        'solution_pk': 'solution__id'
    }

    class Meta:
        model = PossibleImplementationArea
        fields = ('url', 'id', 'solution', 'question', 'geom', 'edit_mask')

    def create(self, validated_data):
        instance = super().create(validated_data)
        return self.makevalid(instance)

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        return self.makevalid(instance)

    def makevalid(self, instance):
        if not instance.geom.valid:
            qs = PossibleImplementationArea.objects.filter(id=instance.id)
            qs.update(geom=CollectionExtract(MakeValid('geom'), 3))
            instance = qs[0]
        return instance


class SolutionSerializer(CreateWithUserInCasestudyMixin,
                         NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'solution_category__keyflow__casestudy__id',
        'keyflow_pk': 'solution_category__keyflow__id'
    }

    solution_category = IDRelatedField()
    currentstate_image = serializers.ImageField(required=False, allow_null=True)
    activities_image = serializers.ImageField(required=False, allow_null=True)
    effect_image = serializers.ImageField(required=False, allow_null=True)
    implementation_count = serializers.SerializerMethodField()
    affected_activities = serializers.SerializerMethodField()

    class Meta:
        model = Solution
        fields = ('url', 'id', 'name', 'description',
                  'documentation', 'solution_category',
                  'activities_image',
                  'currentstate_image', 'effect_image',
                  'implementation_count',
                  'affected_activities'
                  )
        read_only_fields = ('url', 'id', )
        extra_kwargs = {
            'description': {'required': False},
            'documentation': {'required': False},
        }

    def get_implementation_count(self, obj):
        return obj.strategy_set.count()

    def get_affected_activities(self, obj):
        parts = SolutionPart.objects.filter(solution=obj)
        activities = parts.values_list(
            'flow_reference__origin_activity__id',
            'flow_reference__destination_activity__id',
            'flow_changes__origin_activity__id',
            'flow_changes__destination_activity__id',
            'affected_flows__destination_activity__id',
            'affected_flows__origin_activity__id'
        )
        activities = set([i for s in activities for i in s])
        try:
            activities.remove(None)
        except:
            pass
        return activities


class AffectedFlowSerializer(CreateWithUserInCasestudyMixin,
                             serializers.ModelSerializer):

    class Meta:
        model = AffectedFlow
        fields = ('id', 'origin_activity', 'destination_activity',
                  'material', 'process')
        extra_kwargs = {
            'process': {'required': False},
        }


class FlowReferenceSerializer(serializers.ModelSerializer):

    origin_activity = IDRelatedField(
        required=False, allow_null=True)
    destination_activity = IDRelatedField(
        required=False, allow_null=True)
    material = IDRelatedField(
        required=False, allow_null=True)
    process = IDRelatedField(
        required=False, allow_null=True)
    origin_area = IDRelatedField(
        required=False, allow_null=True)
    destination_area = IDRelatedField(
        required=False, allow_null=True)

    class Meta:
        model = FlowReference
        fields = ('origin_activity', 'destination_activity',
                  'material', 'process', 'origin_area',
                  'destination_area')


class SolutionPartSerializer(serializers.ModelSerializer):
    solution = IDRelatedField(read_only=True)
    parent_lookup_kwargs = {
        'casestudy_pk': 'solution__solution_category__keyflow__casestudy__id',
        'keyflow_pk': 'solution__solution_category__keyflow__id',
        'solution_pk': 'solution__id'
    }
    scheme = EnumField(enum=Scheme)
    flow_reference = FlowReferenceSerializer(allow_null=True)
    flow_changes = FlowReferenceSerializer(allow_null=True, required=False)

    affected_flows = AffectedFlowSerializer(many=True)
    question = IDRelatedField(allow_null=True)

    # ToDo: serialize affected flows as part of this serializer

    class Meta:
        model = SolutionPart
        fields = ('id', 'name', 'solution',
                  'scheme', 'documentation',
                  'flow_reference',
                  'flow_changes',
                  'question', 'a', 'b',
                  'priority',
                  'affected_flows',
                  'is_absolute',
                  )
        read_only_fields = ('url', 'id', 'solution')
        extra_kwargs = {
            'documentation': {'required': False, 'allow_blank': True},
            'is_absolute': {'required': False}
        }
        depending_requirements = {
            'scheme': {
                'NEW': [
                    'flow_changes__origin_activity',
                    'flow_changes__destination_activity',
                    'flow_changes__material'
                ],
                'MODIFICATION': [
                    'flow_reference__origin_activity',
                    'flow_reference__destination_activity',
                    'flow_reference__material'
                ],
                'SHIFTDESTINATION': [
                    'flow_reference__origin_activity',
                    'flow_reference__destination_activity',
                    'flow_reference__material',
                    'flow_changes__destination_activity'
                ],
                'SHIFTORIGIN': [
                    'flow_reference__origin_activity',
                    'flow_reference__destination_activity',
                    'flow_reference__material',
                    'flow_changes__origin_activity'
                ],
                'PREPEND': [
                    'flow_reference__origin_activity',
                    'flow_reference__destination_activity',
                    'flow_reference__material',
                    'flow_changes__origin_activity'
                ],
                'APPEND': [
                    'flow_reference__origin_activity',
                    'flow_reference__destination_activity',
                    'flow_reference__material',
                    'flow_changes__destination_activity'
                ],
            }
        }

    def validate(self, data):
        '''
        check fields that are not defined as required but whose requirements
        follows an internal logic depending on scheme
        '''
        request = self.context['request']

        # patching single attributes is going unchecked
        # ToDo: patching might mess up the logic
        if request.method == 'PATCH' and 'scheme' not in data:
            return data

        scheme = data['scheme'].name
        required = self.Meta.depending_requirements['scheme'][scheme]
        errors = {}
        # ToDo: return different message if field is not in data
        error_msg = _('This field may not be blank.')
        for required_field in required:
            subfield = None
            if '__' in required_field:
                required_field, subfield = required_field.split('__')
            value = data.get(required_field, None)
            if not value:
                errors[required_field] = error_msg
            if subfield:
                subvalue = value.get(subfield, '')
                if not subvalue:
                    errors[f'{required_field}__{subfield}'] = error_msg
        question = data.get('question', None)
        if not question and 'is_absolute' not in data:
            errors['is_absolute'] = error_msg
        if len(errors) > 0:
            raise ValidationError(errors)
        return data

    def create(self, validated_data):
        v = validated_data.copy()
        v.pop('affected_flows', None)
        v.pop('flow_reference', None)
        v.pop('flow_changes', None)
        instance = super().create(v)
        return self.update(instance, validated_data)

    def update(self, instance, validated_data):
        affected_flows = validated_data.pop('affected_flows', None)
        flow_reference = validated_data.pop('flow_reference', None)
        flow_changes = validated_data.pop('flow_changes', None)
        instance = super().update(instance, validated_data)
        if affected_flows:
            AffectedFlow.objects.filter(solution_part=instance).delete()
            for f in affected_flows:
                flow = AffectedFlow(solution_part=instance, **f)
                flow.save()
        if flow_reference:
            if instance.flow_reference:
                instance.flow_reference.delete()
            ref_model = FlowReference(**flow_reference)
            ref_model.save()
            instance.flow_reference = ref_model
        if flow_changes:
            if instance.flow_changes:
                instance.flow_changes.delete()
            ref_model = FlowReference(**flow_changes)
            ref_model.save()
            instance.flow_changes = ref_model
        instance.save()
        return instance


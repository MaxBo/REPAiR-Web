from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from repair.apps.asmfa.models import Activity
from repair.apps.changes.models import (SolutionCategory,
                                        Solution,
                                        ImplementationQuestion,
                                        SolutionPart
                                        )

from repair.apps.login.serializers import (InCasestudyField,
                                           UserInCasestudyField,
                                           InCaseStudyIdentityField,
                                           IdentityFieldMixin,
                                           CreateWithUserInCasestudyMixin,
                                           IDRelatedField)
from repair.apps.statusquo.models import SpatialChoice
from repair.apps.utils.serializers import EnumField


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
    unit = IDRelatedField()
    solution = IDRelatedField(read_only=True)
    parent_lookup_kwargs = {
        'casestudy_pk': 'solution__solution_category__keyflow__casestudy__id',
        'keyflow_pk': 'solution__solution_category__keyflow__id',
        'solutioncategory_pk': 'solution__solution_category__id',
        'solution_pk': 'solution__id'
    }

    class Meta:
        model = ImplementationQuestion
        fields = ('url', 'id', 'question', 'unit', 'select_values', 'steps',
                  'min_value', 'max_value', 'is_absolute')
        extra_kwargs = {'steps': {'required': False},
                        'unit': {'required': False},}


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

    class Meta:
        model = Solution
        fields = ('url', 'id', 'name', 'description',
                  'documentation', 'solution_category',
                  'activities_image',
                  'currentstate_image', 'effect_image',
                  'possible_implementation_area'
                  )
        read_only_fields = ('url', 'id', )
        extra_kwargs = {
            'possible_implementation_area': {
                'allow_null': True,
                'required': False,
            },
            'description': {'required': False},
            'documentation': {'required': False},
        }


class SolutionPartSerializer(CreateWithUserInCasestudyMixin,
                             NestedHyperlinkedModelSerializer):
    solution = IDRelatedField(read_only=True)
    parent_lookup_kwargs = {
        'casestudy_pk': 'solution__solution_category__keyflow__casestudy__id',
        'keyflow_pk': 'solution__solution_category__keyflow__id',
        'solution_pk': 'solution__id'
    }
    implementation_flow_origin_activity = IDRelatedField()
    implementation_flow_destination_activity = IDRelatedField()
    implementation_flow_material = IDRelatedField()
    new_target_activity = IDRelatedField(required=False, allow_null=True)
    implementation_flow_spatial_application = EnumField(enum=SpatialChoice)

    # ToDo: serialize affected flows as part of this serializer

    class Meta:
        model = SolutionPart
        fields = ('url', 'id', 'name', 'solution', 'documentation',
                  'implements_new_flow',
                  'implementation_flow_origin_activity',
                  'implementation_flow_destination_activity',
                  'implementation_flow_material',
                  'implementation_flow_process',
                  'implementation_flow_spatial_application',
                  'question', 'a', 'b',
                  'keep_origin', 'new_target_activity',
                  'map_request', 'priority'
                  )
        read_only_fields = ('url', 'id', 'solution')
        extra_kwargs = {
            'implementation_question': {'null': True, 'required': False},
            'keep_origin': {'required': False},
            #'new_target_activity': {'null': True, 'required': False},
            'map_request': {'required': False},
            'documentation': {'required': False, 'allow_blank': True},
            'map_request': {'required': False, 'allow_blank': True}
        }

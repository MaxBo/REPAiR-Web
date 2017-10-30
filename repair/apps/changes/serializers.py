from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from repair.apps.changes.models import (Unit,
                                        SolutionCategory,
                                        Solution,
                                        Implementation,
                                        SolutionInImplementation,
                                        UserInCasestudy,
                                        )

from repair.apps.login.serializers import (UserInCasestudySerializer,
                                           UserInCasestudyField,
                                           InCasestudyField,
                                           InCaseStudyIdentityField,
                                           CreateWithUserInCasestudyMixin)



class SolutionCategoryField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}
    child_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}



class SolutionSetField(InCaseStudyIdentityField):
    lookup_url_kwarg = 'solutioncategory_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'solutioncategory_pk': 'id', }


class SolutionSetSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'solutioncategory_pk': 'solution_category__id',
                            'casestudy_pk': 'solution_category__user__casestudy__id',}
    class Meta:
        model = Solution
        fields = ('url', 'id', 'name')


class SolutionCategorySerializer(CreateWithUserInCasestudyMixin,
                                 NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}
    solution_set = SolutionSetField(
        view_name='solution-list')
    user = UserInCasestudyField(
        view_name='userincasestudy-detail',
        child_lookup_kwargs={'casestudy_pk': 'user__casestudy__id',})

    class Meta:
        model = SolutionCategory
        fields = ('url', 'id', 'name', 'user', 'solution_set')
        read_only_fields = ('url', 'id')


class SolutionCategoryPostSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = SolutionCategory
        fields = ('url', 'id', 'name', 'user')


class SolutionSerializer(CreateWithUserInCasestudyMixin,
                         NestedHyperlinkedModelSerializer):

    parent_lookup_kwargs = {
        'casestudy_pk': 'user__casestudy__id',
        'solutioncategory_pk': 'solution_category__id',
    }
    user = UserInCasestudyField(
        view_name='userincasestudy-detail',
        child_lookup_kwargs={'casestudy_pk': 'user__casestudy__id',})
    solution_category = SolutionCategoryField(
        view_name='solutioncategory-detail',
        child_lookup_kwargs={'casestudy_pk': 'user__casestudy__id',})

    class Meta:
        model = Solution
        fields = ('url', 'id', 'name', 'user', 'description',
                  'one_unit_equals', 'solution_category',
                  #'implementation_set',
                  )
        read_only_fields = ('url', 'id', )


class SolutionPostSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Solution
        fields = ('url', 'id', 'name', 'user', 'description',
                  'one_unit_equals', 'solution_category')


class SolutionInImplementationsField(InCaseStudyIdentityField):
    lookup_url_kwarg = 'implementation_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'implementation_pk': 'id', }


class SolutionInImplementationSetField(InCasestudyField):
    lookup_url_kwarg = 'implementation_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'implementation_pk': 'id', }
    child_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',}


class StakeholderOfImplementaionField(InCaseStudyIdentityField):
    lookup_url_kwarg = 'pk'
    parent_lookup_kwargs = {
        'casestudy_pk': 'user__casestudy__id',
        'pk': 'coordinating_stakeholder__id',
        'stakeholdercategory_pk':
        'coordinating_stakeholder__stakeholder_category__id',}



class ImplementationSerializer(CreateWithUserInCasestudyMixin,
                               NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}
    solution_list = SolutionInImplementationsField(source='solution',
        view_name='solutioninimplementation-list')
    solutions = SolutionInImplementationSetField(
        view_name='solutioninimplementation-detail',
        many=True,
        child_lookup_kwargs={'casestudy_pk': 'user__casestudy__id',})
    coordinating_stakeholder = StakeholderOfImplementaionField(
        view_name='stakeholder-detail')
    user = UserInCasestudyField(
        view_name='userincasestudy-detail',
        child_lookup_kwargs={'casestudy_pk': 'user__casestudy__id',})
    class Meta:
        model = Implementation
        fields = ('url', 'id', 'name', 'user', 'solutions',
                  'coordinating_stakeholder',
                  'solution_list',
                  )
        read_only_fields = ('url', 'id', 'solutions')

    def update(self, obj, validated_data):
        """
        update the implementation-attributes,
        including selected solutions
        """
        implementation = obj
        implementation_id = implementation.id

        # handle solutions
        new_solutions = validated_data.pop('solutions', None)
        if new_solutions is not None:
            SolutionInImplementationModel = Implementation.solutions.through
            solution_qs = SolutionInImplementationModel.objects.filter(
                implementation=implementation)
            # delete existing solutions
            solution_qs.exclude(solution_id__in=(
                sol.id for sol in new_solutions)).delete()
            # add or update new solutions
            for sol in new_solutions:
                SolutionInImplementationModel.objects.update_or_create(
                    implementation=implementation,
                    solution=sol)

        # update other attributes
        obj.__dict__.update(**validated_data)
        obj.save()
        return obj


class ImplementationField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}
    child_lookup_kwargs = {'casestudy_pk': 'implementation__user__casestudy__id'}


class SolutionField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'solution_category__user__casestudy__id',
                            'solutioncategory_pk': 'solution_category__id',}
    child_lookup_kwargs = {'casestudy_pk': 'implementation__user__casestudy__id',
                           'implementation_pk': 'implementation__id',}



class SolutionInImplementationSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk':
                            'implementation__user__casestudy__id',
                            'implementation_pk': 'implementation__id',
                            }
    implementation = ImplementationField(view_name='implementation-detail')
    solution = SolutionField(view_name='solution-detail')
    class Meta:
        model = SolutionInImplementation
        fields = ('url', 'id',
                  'implementation',
                  'solution')


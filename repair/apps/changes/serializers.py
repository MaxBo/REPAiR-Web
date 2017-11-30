from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from repair.apps.changes.models import (Unit,
                                        SolutionCategory,
                                        Solution,
                                        Implementation,
                                        SolutionInImplementation,
                                        SolutionQuantity,
                                        SolutionRatioOneUnit,
                                        SolutionInImplementationNote,
                                        SolutionInImplementationQuantity,
                                        SolutionInImplementationGeometry,
                                        Strategy,
                                        )

from repair.apps.login.serializers import (InCasestudyField,
                                           UserInCasestudyField,
                                           InSolutionField,
                                           InCaseStudyIdentityField,
                                           IdentityFieldMixin,
                                           CreateWithUserInCasestudyMixin)



class UnitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Unit
        fields = ('url', 'id', 'name')


class SolutionCategoryField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}


class SolutionField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk':
                            'solution_category__user__casestudy__id',
                            'solutioncategory_pk': 'solution_category__id',}
    extra_lookup_kwargs = {'casestudy_pk':
                           'implementation__user__casestudy__id'}


class SolutionSetField(InCasestudyField):
    """Returns a List of links to the solutions"""
    lookup_url_kwarg = 'solutioncategory_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'solution_category__user__casestudy__id',
                            'solutioncategory_pk': 'solution_category__id', }


class SolutionListField(IdentityFieldMixin, SolutionSetField):
    """Returns a Link to the solutions--list view"""
    lookup_url_kwarg = 'solutioncategory_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'solutioncategory_pk': 'id', }


class SolutionSetSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'solutioncategory_pk': 'solution_category__id',
                            'casestudy_pk':
                            'solution_category__user__casestudy__id',}
    class Meta:
        model = Solution
        fields = ('url', 'id', 'name')


class UnitField(serializers.HyperlinkedRelatedField):
    """A Unit Field"""
    queryset = Unit.objects


class SolutionCategorySerializer(CreateWithUserInCasestudyMixin,
                                 NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}
    solution_set = SolutionListField(
        view_name='solution-list')
    solution_list = SolutionSetField(
        source='solution_set',
        view_name='solution-detail',
        many=True,
        read_only=True,
    )
    user = UserInCasestudyField(
        view_name='userincasestudy-detail',
    )

    class Meta:
        model = SolutionCategory
        fields = ('url', 'id', 'name', 'user', 'solution_set', 'solution_list')
        read_only_fields = ('url', 'id')


class SolutionCategoryPostSerializer(SolutionCategorySerializer):
    class Meta:
        model = SolutionCategory
        fields = ('url', 'id', 'name', 'user', 'solution_set', 'solution_list')
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


class SolutionQuantitySerializer(SolutionDetailCreateMixin,
                                 #CreateWithUserInCasestudyMixin,
                                 NestedHyperlinkedModelSerializer):
    unit = UnitField(view_name='unit-detail')
    solution = SolutionField(view_name='solution-detail', read_only=True)
    parent_lookup_kwargs = {
        'casestudy_pk': 'solution__user__casestudy__id',
        'solutioncategory_pk': 'solution__solution_category__id',
        'solution_pk': 'solution__id',
    }
    class Meta:
        model = SolutionQuantity
        fields = ('url', 'id', 'name', 'unit', 'solution')



class SolutionDetailListField(InCaseStudyIdentityField):
    lookup_url_kwarg = 'solution_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'solutioncategory_pk': 'solution_category__id',
                            'solution_pk': 'id',
                            }


class SolutionRatioOneUnitSerializer(SolutionDetailCreateMixin,
                                     NestedHyperlinkedModelSerializer):
    unit = UnitField(view_name='unit-detail')
    solution = SolutionField(view_name='solution-detail', read_only=True)
    value = serializers.DecimalField(max_digits=10, decimal_places=3)
    parent_lookup_kwargs = {
        'casestudy_pk': 'solution__user__casestudy__id',
        'solutioncategory_pk': 'solution__solution_category__id',
        'solution_pk': 'solution__id',
    }
    class Meta:
        model = SolutionRatioOneUnit
        fields = ('url', 'id', 'name', 'value', 'unit', 'solution')



class SolutionSerializer(CreateWithUserInCasestudyMixin,
                         NestedHyperlinkedModelSerializer):

    parent_lookup_kwargs = {
        'casestudy_pk': 'user__casestudy__id',
        'solutioncategory_pk': 'solution_category__id',
    }
    user = UserInCasestudyField(view_name='userincasestudy-detail')
    solution_category = SolutionCategoryField(
        view_name='solutioncategory-detail')
    solutionquantity_set = SolutionDetailListField(
        view_name='solutionquantity-list')
    solutionratiooneunit_set = SolutionDetailListField(
        view_name='solutionratiooneunit-list')

    class Meta:
        model = Solution
        fields = ('url', 'id', 'name', 'user', 'description',
                  'one_unit_equals', 'solution_category',
                  'solutionquantity_set',
                  'solutionratiooneunit_set',
                  #'solution_category_id',
                  #'implementation_set',
                  )
        read_only_fields = ('url', 'id', )


class SolutionInImplementationSetField(InCasestudyField):
    """Returns a list of links to the solutions"""
    lookup_url_kwarg = 'implementation_pk'
    parent_lookup_kwargs = {
        'casestudy_pk': 'implementation__user__casestudy__id',
        'implementation_pk': 'implementation__id', }


class ImplementationInStrategySetField(InCasestudyField):
    """Returns a list of links to the solutions"""
    lookup_url_kwarg = 'casestudy_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}


class SolutionIISetField(InCasestudyField):
    """Returns a list of links to the solutions"""
    lookup_url_kwarg = 'solutioncategory_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'solutioncategory_pk': 'id', }


class SolutionInImplementationsListField(IdentityFieldMixin,
                                         SolutionInImplementationSetField):
    """Returns a Link to the solutions--list view"""
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'implementation_pk': 'id', }


class ImplementationInStrategiesListField(IdentityFieldMixin,
                                         ImplementationInStrategySetField):
    """Returns a Link to the implementations--list view"""
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}


class StakeholderOfImplementationField(InCaseStudyIdentityField):
    lookup_url_kwarg = 'pk'
    parent_lookup_kwargs = {
        'casestudy_pk': 'user__casestudy__id',
        'pk': 'coordinating_stakeholder__id',
        'stakeholdercategory_pk':
        'coordinating_stakeholder__stakeholder_category__id',}


class StakeholderOfStrategyField(InCaseStudyIdentityField):
    lookup_url_kwarg = 'pk'
    parent_lookup_kwargs = {
        'casestudy_pk': 'user__casestudy__id',
        'pk': 'coordinator__id',
        'stakeholdercategory_pk':
        'coordinator__stakeholder_category__id',}


class ImplementationSerializer(CreateWithUserInCasestudyMixin,
                               NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}
    solution_list = SolutionInImplementationsListField(
        source='solutioninimplementation_set',
        view_name='solutioninimplementation-list')
    sii_set = SolutionInImplementationSetField(
        source='solutioninimplementation_set',
        view_name='solutioninimplementation-detail',
        many=True,
        read_only=True)
    solution_set = SolutionIISetField(
        source='solutions',
        view_name='solution-detail',
        many=True)
    coordinating_stakeholder = StakeholderOfImplementationField(
        view_name='stakeholder-detail')
    user = UserInCasestudyField(
        view_name='userincasestudy-detail')

    class Meta:
        model = Implementation
        fields = ('url', 'id', 'name', 'user',
                  'coordinating_stakeholder',
                  'solution_set',
                  'solution_list',
                  'sii_set',
                  )

    def update(self, obj, validated_data):
        """
        update the implementation-attributes,
        including selected solutions
        """
        implementation = obj

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
        for attr, value in validated_data.items():
            setattr(obj, attr, value)
        obj.save()
        return obj


class ImplementationOfUserSerializer(ImplementationSerializer):
    """"""
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'user_pk': 'user__id',}


class ImplementationField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}
    extra_lookup_kwargs = {'casestudy_pk':
                           'implementation__user__casestudy__id'}


class SolutionInImplementationDetailListField(InCaseStudyIdentityField):
    lookup_url_kwarg = 'solution_pk'
    parent_lookup_kwargs = {'casestudy_pk':
                            'implementation__user__casestudy__id',
                            'implementation_pk': 'implementation__id',
                            'solution_pk': 'id',
                            }


class SolutionInImplementationSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk':
                            'implementation__user__casestudy__id',
                            'implementation_pk': 'implementation__id',
                            }
    implementation = ImplementationField(
        view_name='implementation-detail')
    solution = SolutionField(view_name='solution-detail')
    solutioninimplementationnote_set = SolutionInImplementationDetailListField(
        view_name='solutioninimplementationnote-list')
    solutioninimplementationquantity_set = SolutionInImplementationDetailListField(
        view_name='solutioninimplementationquantity-list')
    solutioninimplementationgeometry_set = SolutionInImplementationDetailListField(
        view_name='solutioninimplementationgeometry-list')


    class Meta:
        model = SolutionInImplementation
        fields = ('url', 'id',
                  'implementation',
                  'solution',
                  'solutioninimplementationnote_set',
                  'solutioninimplementationquantity_set',
                  'solutioninimplementationgeometry_set',
                  )


class SolutionInImplementationField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'implementation__user__casestudy__id',
        'implementation_pk': 'implementation__id',}


class SolutionInImplementationDetailCreateMixin:
    def create(self, validated_data):
        """Create a new solution quantity"""
        url_pks = self.context['request'].session['url_pks']
        solution_pks = url_pks['solution_pk']
        sii = SolutionInImplementation.objects.get(id=solution_pks)

        obj = self.Meta.model.objects.create(
            sii=sii,
            **validated_data)
        return obj


class SolutionInImplementationNoteSerializer(SolutionInImplementationDetailCreateMixin,
                                             NestedHyperlinkedModelSerializer):
    sii = SolutionInImplementationField(
        view_name='solutioninimplementation-detail',
        read_only=True)
    parent_lookup_kwargs = {
        'casestudy_pk': 'sii__implementation__user__casestudy__id',
        'implementation_pk': 'sii__implementation__id',
        'solution_pk': 'sii__id',
    }
    class Meta:
        model = SolutionInImplementationNote
        fields = ('url', 'id', 'note', 'sii')


class SolutionQuantityField(InSolutionField):
    parent_lookup_kwargs = {'casestudy_pk':
                            'solution__solution_category__user__casestudy__id',
                            'solutioncategory_pk': 'solution__solution_category__id',
                            'solution_pk': 'solution__id',}


class SolutionInImplementationQuantitySerializer(SolutionInImplementationNoteSerializer):
    quantity = SolutionQuantityField(view_name='solutionquantity-detail',
                                     help_text=_('the quantity to define'),
                                     label=_('Solution Quantity'))
    class Meta:
        model = SolutionInImplementationQuantity
        fields = ('url', 'id', 'quantity', 'value', 'sii')


class SolutionInImplementationGeometrySerializer(SolutionInImplementationNoteSerializer):
    class Meta:
        model = SolutionInImplementationGeometry
        fields = ('url', 'id', 'name', 'geom', 'sii')


class StrategySerializer(CreateWithUserInCasestudyMixin,
                         NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}
    implementation_list = ImplementationInStrategiesListField(
        source='implementations',
        view_name='implementation-list')
    implementation_set = ImplementationInStrategySetField(
        source='implementations',
        view_name='implementation-detail',
        many=True)
    coordinator = StakeholderOfStrategyField(
        view_name='stakeholder-detail')
    user = UserInCasestudyField(
        view_name='userincasestudy-detail')

    class Meta:
        model = Strategy
        fields = ('url', 'id', 'name', 'user',
                  'coordinator',
                  'implementation_set',
                  'implementation_list',
                  )

    def update(self, obj, validated_data):
        """
        update the stratagy-attributes,
        including selected solutions
        """
        strategy = obj

        # handle implementations
        new_implementations = validated_data.pop('implementations', None)
        if new_implementations is not None:
            ImplementationInStrategyModel = Strategy.implementations.through
            implementation_qs = ImplementationInStrategyModel.objects.filter(
                strategy=strategy)
            # delete existing solutions
            implementation_qs.exclude(implementation_id__in=(
                impl.id for impl in new_implementations)).delete()
            # add or update new solutions
            for impl in new_implementations:
                ImplementationInStrategyModel.objects.update_or_create(
                    implementation=impl,
                    strategy=strategy)

        # update other attributes
        for attr, value in validated_data.items():
            setattr(obj, attr, value)
        obj.save()
        return obj

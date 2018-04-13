from django.utils.translation import ugettext_lazy as _
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from rest_framework import serializers

from repair.apps.changes.models import (Implementation,
                                        SolutionInImplementation,
                                        SolutionInImplementationQuantity,
                                        )

from repair.apps.login.serializers import (InCasestudyField,
                                           UserInCasestudyField,
                                           InSolutionField,
                                           InCaseStudyIdentityField,
                                           IdentityFieldMixin,
                                           CreateWithUserInCasestudyMixin,
                                           IDRelatedField)


from .solutions import SolutionField


class SolutionInImplementationSetField(InCasestudyField):
    """Returns a list of links to the solutions"""
    lookup_url_kwarg = 'implementation_pk'
    parent_lookup_kwargs = {
        'casestudy_pk': 'implementation__user__casestudy__id',
        'implementation_pk': 'implementation__id', }


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


class StakeholderOfImplementationField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'stakeholder_category__casestudy__id',
        'stakeholdercategory_pk': 'stakeholder_category__id', }


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
    coordinating_stakeholder = IDRelatedField()
    user = IDRelatedField(read_only=True)

    class Meta:
        model = Implementation
        fields = ('url', 'id', 'name', 'user',
                  'coordinating_stakeholder',
                  'solution_list',
                  'sii_set',
                  )

    def update(self, instance, validated_data):
        """
        update the implementation-attributes,
        including selected solutions
        """
        implementation = instance

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
            setattr(instance, attr, value)
        instance.save()
        return instance


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
        view_name='implementation-detail', read_only=True)
    solution = IDRelatedField()
    solutioninimplementationquantity_set = SolutionInImplementationDetailListField(
        view_name='solutioninimplementationquantity-list')

    class Meta:
        model = SolutionInImplementation
        fields = ('url', 'id',
                  'implementation',
                  'solution',
                  'solutioninimplementationquantity_set',
                  'note', 'geom'
                  )


class SolutionInImplementationField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'implementation__user__casestudy__id',
        'implementation_pk': 'implementation__id', }


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


class SolutionInImplementationChildSerializer(SolutionInImplementationDetailCreateMixin,
                                             NestedHyperlinkedModelSerializer):
    sii = SolutionInImplementationField(
        view_name='solutioninimplementation-detail',
        read_only=True)
    parent_lookup_kwargs = {
        'casestudy_pk': 'sii__implementation__user__casestudy__id',
        'implementation_pk': 'sii__implementation__id',
        'solution_pk': 'sii__id', }


class SolutionQuantityField(InSolutionField):
    parent_lookup_kwargs = {'casestudy_pk':
                            'solution__solution_category__user__casestudy__id',
                            'solutioncategory_pk': 'solution__solution_category__id',
                            'solution_pk': 'solution__id', }


class SolutionInImplementationQuantitySerializer(SolutionInImplementationChildSerializer):
    quantity = SolutionQuantityField(view_name='solutionquantity-detail',
                                     help_text=_('the quantity to define'),
                                     label=_('Solution Quantity'),
                                     read_only=True)
    name = serializers.CharField(source='quantity.name', read_only=True)
    unit = serializers.CharField(source='quantity.unit.name', read_only=True)

    class Meta:
        model = SolutionInImplementationQuantity
        fields = ('url', 'id', 'name', 'unit', 'quantity', 'value', 'sii')
        read_only_fields = ('quantity', 'sii')


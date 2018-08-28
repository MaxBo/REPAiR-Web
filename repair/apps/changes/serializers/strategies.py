from django.utils.translation import ugettext_lazy as _
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from rest_framework import serializers

from repair.apps.changes.models import (Strategy,
                                        SolutionInStrategy,
                                        SolutionInStrategyQuantity,
                                        )

from repair.apps.login.serializers import (InCasestudyField,
                                           UserInCasestudyField,
                                           InSolutionField,
                                           InCaseStudyIdentityField,
                                           IdentityFieldMixin,
                                           CreateWithUserInCasestudyMixin,
                                           IDRelatedField)


from .solutions import SolutionField


class SolutionInStrategySetField(InCasestudyField):
    """Returns a list of links to the solutions"""
    lookup_url_kwarg = 'strategy_pk'
    parent_lookup_kwargs = {
        'casestudy_pk': 'strategy__user__casestudy__id',
        'strategy_pk': 'strategy__id', }


class SolutionIISetField(InCasestudyField):
    """Returns a list of links to the solutions"""
    lookup_url_kwarg = 'solutioncategory_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'solutioncategory_pk': 'id', }


class SolutionInStrategyListField(IdentityFieldMixin,
                                  SolutionInStrategySetField):
    """Returns a Link to the solutions--list view"""
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'strategy_pk': 'id', }


class StakeholderOfStrategyField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'stakeholder_category__casestudy__id',
        'stakeholdercategory_pk': 'stakeholder_category__id', }


class StrategySerializer(CreateWithUserInCasestudyMixin,
                         NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}
    solution_list = SolutionInStrategyListField(
        source='solutioninstrategy_set',
        view_name='solutioninstrategy-list')
    sii_set = SolutionInStrategySetField(
        source='solutioninstrategy_set',
        view_name='solutioninstrategy-detail',
        many=True,
        read_only=True)
    coordinating_stakeholder = IDRelatedField()
    user = IDRelatedField(read_only=True)

    class Meta:
        model = Strategy
        fields = ('url', 'id', 'name', 'user',
                  'coordinating_stakeholder',
                  'solution_list',
                  'sii_set',
                  )

    def update(self, instance, validated_data):
        """
        update the strategy-attributes,
        including selected solutions
        """
        strategy = instance

        # handle solutions
        new_solutions = validated_data.pop('solutions', None)
        if new_solutions is not None:
            SolutionInStrategyModel = Strategy.solutions.through
            solution_qs = SolutionInStrategyModel.objects.filter(
                strategy=strategy)
            # delete existing solutions
            solution_qs.exclude(solution_id__in=(
                sol.id for sol in new_solutions)).delete()
            # add or update new solutions
            for sol in new_solutions:
                SolutionInStrategyModel.objects.update_or_create(
                    strategy=strategy,
                    solution=sol)

        # update other attributes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class StrategyField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}
    extra_lookup_kwargs = {'casestudy_pk':
                           'strategy__user__casestudy__id'}


class SolutionInStrategyDetailListField(InCaseStudyIdentityField):
    lookup_url_kwarg = 'solution_pk'
    parent_lookup_kwargs = {'casestudy_pk':
                            'strategy__user__casestudy__id',
                            'strategy_pk': 'strategy__id',
                            'solution_pk': 'id',
                            }


class SolutionInStrategySerializer(serializers.ModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk':
                            'strategy__user__casestudy__id',
                            'strategy_pk': 'strategy__id',
                            }
    participants = IDRelatedField(many=True, required=False)

    class Meta:
        model = SolutionInStrategy
        fields = ('id',
                  'solution',
                  'note', 'geom',
                  'participants'
                  )


class SolutionInStrategyField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'strategy__user__casestudy__id',
        'strategy_pk': 'strategy__id', }


class SolutionInStrategyDetailCreateMixin:
    def create(self, validated_data):
        """Create a new solution quantity"""
        url_pks = self.context['request'].session['url_pks']
        solution_pks = url_pks['solution_pk']
        sii = SolutionInStrategy.objects.get(id=solution_pks)

        obj = self.Meta.model.objects.create(
            sii=sii,
            **validated_data)
        return obj


class SolutionInStrategyChildSerializer(SolutionInStrategyDetailCreateMixin,
                                             NestedHyperlinkedModelSerializer):
    sii = SolutionInStrategyField(
        view_name='solutioninstrategy-detail',
        read_only=True)
    parent_lookup_kwargs = {
        'casestudy_pk': 'sii__strategy__user__casestudy__id',
        'strategy_pk': 'sii__strategy__id',
        'solution_pk': 'sii__id', }


class SolutionQuantityField(InSolutionField):
    parent_lookup_kwargs = {'casestudy_pk':
                            'solution__solution_category__user__casestudy__id',
                            'solutioncategory_pk': 'solution__solution_category__id',
                            'solution_pk': 'solution__id', }


class SolutionInStrategyQuantitySerializer(SolutionInStrategyChildSerializer):
    quantity = SolutionQuantityField(view_name='solutionquantity-detail',
                                     help_text=_('the quantity to define'),
                                     label=_('Solution Quantity'),
                                     read_only=True)
    name = serializers.CharField(source='quantity.name', read_only=True)
    unit = serializers.CharField(source='quantity.unit.name', read_only=True)

    class Meta:
        model = SolutionInStrategyQuantity
        fields = ('url', 'id', 'name', 'unit', 'quantity', 'value', 'sii')
        read_only_fields = ('quantity', 'sii')


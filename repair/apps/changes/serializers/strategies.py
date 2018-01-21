
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from repair.apps.changes.models import Strategy

from repair.apps.login.serializers import (InCasestudyField,
                                           UserInCasestudyField,
                                           InCaseStudyIdentityField,
                                           IdentityFieldMixin,
                                           CreateWithUserInCasestudyMixin)


class StakeholderOfStrategyField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'stakeholder_category__casestudy__id',
        'stakeholdercategory_pk': 'stakeholder_category__id', }


class ImplementationInStrategySetField(InCasestudyField):
    """Returns a list of links to the solutions"""
    lookup_url_kwarg = 'casestudy_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}


class ImplementationInStrategiesListField(IdentityFieldMixin,
                                          ImplementationInStrategySetField):
    """Returns a Link to the implementations--list view"""
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}


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

    def update(self, instance, validated_data):
        """
        update the stratagy-attributes,
        including selected solutions
        """
        strategy = instance

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
            setattr(instance, attr, value)
        instance.save()
        return instance

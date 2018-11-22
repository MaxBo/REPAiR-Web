from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

from repair.apps.login.models import CaseStudy
from repair.apps.asmfa.models import (Keyflow,
                                      KeyflowInCasestudy,
                                      Product,
                                      ProductFraction,
                                      Material,
                                      Waste,
                                      Composition
                                      )

from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           InCasestudySerializerMixin,
                                           InCasestudyField,
                                           InCasestudyListField,
                                           IdentityFieldMixin,
                                           NestedHyperlinkedRelatedField,
                                           IDRelatedField)


class InCasestudyKeyflowListField(InCasestudyListField):
    """
    Field that returns a list of all items in the keyflow in the casestudy
    """
    lookup_url_kwarg = 'keyflow_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id',
                            'keyflow_pk': 'id'}


class KeyflowSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    casestudies = serializers.HyperlinkedRelatedField(
        queryset=CaseStudy.objects,
        many=True,
        view_name='casestudy-detail',
        help_text=_('Select the Casestudies the Keyflow is used in')
    )

    class Meta:
        model = Keyflow
        fields = ('url', 'id', 'code', 'name', 'casestudies',
                  )

    def update(self, instance, validated_data):
        """update the user-attributes, including profile information"""
        keyflow = instance

        # handle groups
        new_casestudies = validated_data.pop('casestudies', None)
        if new_casestudies is not None:
            ThroughModel = Keyflow.casestudies.through
            casestudy_qs = ThroughModel.objects.filter(
                keyflow=keyflow.id)
            # delete existing groups
            casestudy_qs.exclude(
                casestudy__id__in=(cs.id for cs in new_casestudies)).delete()
            # add or update new groups
            for cs in new_casestudies:
                ThroughModel.objects.update_or_create(keyflow=keyflow,
                                                      casestudy=cs)

        # update other attributes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def create(self, validated_data):
        """Create a new Keyflow"""
        code = validated_data.pop('code')

        keyflow = Keyflow.objects.create(code=code)
        self.update(instance=keyflow, validated_data=validated_data)
        return keyflow


class InKeyflowField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk':
        'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id', }
    extra_lookup_kwargs = {}
    filter_field = 'keyflow_pk'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url_pks_lookup['keyflow_pk'] = \
            self.parent_lookup_kwargs['keyflow_pk']


class InKeyflowSetField(IdentityFieldMixin, InKeyflowField, ):
    """Field that returns a list of all items in the casestudy"""
    lookup_url_kwarg = 'keyflow_pk'
    parent_lookup_kwargs = {
        'casestudy_pk': 'casestudy__id',
        'keyflow_pk': 'id', }


class KeyflowField(NestedHyperlinkedRelatedField):
    parent_lookup_kwargs = {'pk': 'id'}
    queryset = Keyflow.objects
    """This is fixed in rest_framework_nested, but not yet available on pypi"""
    def use_pk_only_optimization(self):
        return False


class KeyflowInCasestudySerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    note = serializers.CharField(required=False, allow_blank=True)
    casestudy = IDRelatedField()
    keyflow = IDRelatedField()
    groupstock_set = InKeyflowSetField(view_name='groupstock-list')
    group2group_set = InKeyflowSetField(view_name='group2group-list')
    activitystock_set = InKeyflowSetField(view_name='activitystock-list')
    activity2activity_set = InKeyflowSetField(view_name='activity2activity-list')
    actorstock_set = InKeyflowSetField(view_name='actorstock-list')
    actor2actor_set = InKeyflowSetField(view_name='actor2actor-list')

    activitygroups = InCasestudyKeyflowListField(view_name='activitygroup-list')
    activities = InCasestudyKeyflowListField(view_name='activity-list')
    actors = InCasestudyKeyflowListField(view_name='actor-list')
    administrative_locations = InCasestudyKeyflowListField(
        view_name='administrativelocation-list')
    operational_locations = InCasestudyKeyflowListField(
        view_name='operationallocation-list')

    code = serializers.CharField(source='keyflow.code',
                                 allow_blank=True, required=False)
    name = serializers.CharField(source='keyflow.name',
                                 allow_blank=True, required=False)

    class Meta:
        model = KeyflowInCasestudy
        fields = ('url',
                  'id',
                  'keyflow',
                  'casestudy',
                  'note',
                  'groupstock_set',
                  'group2group_set',
                  'activitystock_set',
                  'activity2activity_set',
                  'actorstock_set',
                  'actor2actor_set',
                  'code',
                  'note',
                  'name',
                  'activitygroups',
                  'activities',
                  'actors',
                  'administrative_locations',
                  'operational_locations',
                  )


class KeyflowInCasestudyPostSerializer(InCasestudySerializerMixin,
                                       NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    note = serializers.CharField(required=False, allow_blank=True)
    keyflow = IDRelatedField()

    class Meta:
        model = KeyflowInCasestudy
        fields = ('keyflow',
                  'note',
                  )


class KeyflowInCasestudyDetailCreateMixin:
    def create(self, validated_data):
        """Create a new solution quantity"""
        url_pks = self.context['request'].session['url_pks']
        keyflow_pk = url_pks['keyflow_pk']
        # ToDo: raise some kind of exception or prevent creating object with
        # wrong keyflow/casestudy combination somewhere else (view.update?)
        # atm the server will just hang up here
        mic = KeyflowInCasestudy.objects.get(id=keyflow_pk)
        validated_data['keyflow'] = mic

        obj = self.Meta.model.objects.create(
            **validated_data)
        return obj


class KeyflowInCasestudyField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id',
                            }


class ProductInKeyflowInCasestudyField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }


class ProductFractionSerializer(serializers.ModelSerializer):
    publication = IDRelatedField(allow_null=True, required=False)
    id = serializers.IntegerField(label='ID', read_only=False, required=False,
                                  allow_null=True)
    parent_lookup_kwargs = {}

    class Meta:
        model = ProductFraction
        fields = ('id',
                  'composition',
                  'material',
                  'fraction',
                  'publication',
                  'avoidable')
        read_only_fields = ['composition']


class CompositionSerializer(NestedHyperlinkedModelSerializer):
    fractions = ProductFractionSerializer(many=True)
    id = serializers.IntegerField(label='ID', read_only=False, required=False,
                                  allow_null=True)
    keyflow = IDRelatedField(read_only=True)
    parent_lookup_kwargs = {}

    class Meta:
        model = Composition
        fields = ('id',
                  'name',
                  'nace',
                  'fractions',
                  'keyflow')

    def create(self, validated_data):
        fractions = validated_data.pop('fractions')
        instance = super().create(validated_data)
        validated_data['fractions'] = fractions
        self.update(instance, validated_data)
        return instance

    def update(self, instance, validated_data):
        """update the user-attributes, including fraction information"""
        composition = instance

        # handle product fractions
        new_fractions = validated_data.pop('fractions', None)

        if new_fractions is not None:
            product_fractions = ProductFraction.objects.filter(
                composition=composition)
            # delete existing rows not needed any more
            ids = [fraction.get('id') for fraction in new_fractions if fraction.get('id') is not None]
            to_delete = product_fractions.exclude(id__in=ids)
            to_delete.delete()
            # add or update new fractions
            for new_fraction in new_fractions:
                material_id = getattr(new_fraction.get('material'), 'id')
                material = Material.objects.get(id=material_id)
                fraction_id = new_fraction.get('id')
                # create new fraction
                if (fraction_id is None or
                    len(product_fractions.filter(id=fraction_id)) == 0):
                    fraction = ProductFraction(composition=composition)
                # change existing fraction
                else:
                    fraction = product_fractions.get(id=fraction_id)

                for attr, value in new_fraction.items():
                    if attr in ('composition', 'id'):
                        continue
                    setattr(fraction, attr, value)
                fraction.save()

        # update other attributes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ProductSerializer(CompositionSerializer):

    class Meta:
        model = Product
        fields = ('url', 'id', 'name', 'nace', 'cpa',
                  'fractions', 'keyflow'
                  )


class WasteSerializer(CompositionSerializer):

    class Meta:
        model = Waste
        fields = ('url', 'id', 'name', 'nace', 'ewc', 'wastetype', 'hazardous',
                  'fractions', 'keyflow')


class AllMaterialSerializer(serializers.ModelSerializer):
    #keyflow = IDRelatedField(allow_null=True)
    parent = IDRelatedField(allow_null=True)
    level = serializers.IntegerField(required=False, default=0)

    class Meta:
        model = Material
        fields = ('url', 'id', 'name', 'keyflow', 'level', 'parent')


class MaterialSerializer(KeyflowInCasestudyDetailCreateMixin,
                         AllMaterialSerializer):
    # keyflow filtering is done by "get_queryset"
    parent_lookup_kwargs = {}
    class Meta:
        model = Material
        fields = ('id', 'name', 'level', 'parent', 'keyflow')


class AllMaterialListSerializer(AllMaterialSerializer):
    class Meta(AllMaterialSerializer.Meta):
        fields = ('id', 'name', 'level', 'parent', 'keyflow')


class MaterialListSerializer(MaterialSerializer):
    class Meta(MaterialSerializer.Meta):
        fields = ('id', 'name', 'level', 'parent', 'keyflow')

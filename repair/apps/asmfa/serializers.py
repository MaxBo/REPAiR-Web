from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

from repair.apps.login.models import CaseStudy
from repair.apps.asmfa.models import (ActivityGroup,
                                      Activity,
                                      Actor,
                                      Flow,
                                      Stock,
                                      Actor2Actor,
                                      Activity2Activity,
                                      Group2Group,
                                      Material,
                                      Quality,
                                      MaterialInCasestudy,
                                      GroupStock,
                                      ActivityStock,
                                      ActorStock,
                                      )
from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           InCasestudyField,
                                           InCaseStudyIdentityField,
                                           InCasestudyListField,
                                           IdentityFieldMixin,
                                           CreateWithUserInCasestudyMixin,
                                           NestedHyperlinkedRelatedField,
                                           IDRelatedField)


class MaterialSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    casestudies = serializers.HyperlinkedRelatedField(
        queryset = CaseStudy.objects.all(),
        many=True,
        view_name='casestudy-detail',
        help_text=_('Select the Casestudies the material is used in')
    )

    class Meta:
        model = Material
        fields = ('url', 'id', 'code', 'name', 'casestudies')


    def update(self, obj, validated_data):
        """update the user-attributes, including profile information"""
        material = obj

        # handle groups
        new_casestudies = validated_data.pop('casestudies', None)
        if new_casestudies is not None:
            MaterialInCasestudy = Material.casestudies.through
            casestudy_qs = MaterialInCasestudy.objects.filter(
                material=material.id)
            # delete existing groups
            casestudy_qs.exclude(
                casestudy__id__in=(cs.id for cs in new_casestudies)).delete()
            # add or update new groups
            for cs in new_casestudies:
                MaterialInCasestudy.objects.update_or_create(material=material,
                                                             casestudy=cs)

        # update other attributes
        obj.__dict__.update(**validated_data)
        obj.save()
        return obj

    def create(self, validated_data):
        """Create a new material"""
        code = validated_data.pop('code')

        material = Material.objects.create(code=code)
        self.update(obj=material, validated_data=validated_data)
        return material


class QualitySerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}

    class Meta:
        model = Quality
        fields = ('url', 'id', 'name')


class InMaterialField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk':
        'material__casestudy__id',
        'material_pk': 'material__id',}
    extra_lookup_kwargs = {}
    filter_field = 'material_pk'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.casestudy_pk_lookup['material_pk'] = \
            self.parent_lookup_kwargs['material_pk']


class InMaterialSetField(IdentityFieldMixin, InMaterialField, ):
    """Field that returns a list of all items in the casestudy"""
    lookup_url_kwarg = 'material_pk'
    parent_lookup_kwargs = {
        'casestudy_pk':
        'casestudy__id',
        'material_pk': 'id',}


class MaterialField(NestedHyperlinkedRelatedField):
    parent_lookup_kwargs = {'pk': 'id'}
    queryset = Material.objects.all()
    """This is fixed in rest_framework_nested, but not yet available on pypi"""
    def use_pk_only_optimization(self):
        return False


class MaterialInCasestudySerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    note = serializers.CharField(required=False, allow_blank=True)
    material = MaterialSerializer(read_only=True)
    groupstock_set = InMaterialSetField(view_name='groupstock-list')
    group2group_set = InMaterialSetField(view_name='group2group-list')
    activitystock_set = InMaterialSetField(view_name='activitystock-list')
    activity2activity_set = InMaterialSetField(view_name='activity2activity-list')
    actorstock_set = InMaterialSetField(view_name='actorstock-list')
    actor2actor_set = InMaterialSetField(view_name='actor2actor-list')

    class Meta:
        model = MaterialInCasestudy
        fields = ('url',
                  'id',
                  'material',
                  'note',
                  'groupstock_set',
                  'group2group_set',
                  'activitystock_set',
                  'activity2activity_set',
                  'actorstock_set',
                  'actor2actor_set')


class MaterialInCasestudyDetailCreateMixin:
    def create(self, validated_data):
        """Create a new solution quantity"""
        # Note by Christoph: why is the material_pk in session['casestudy_pk'] 
        # alongside with the key casestudy_pk?
        # is it supposed to be this way?
        casestudy_session = self.context['request'].session['casestudy_pk']
        casestudy_pk = casestudy_session['casestudy_pk']
        material_pk = casestudy_session['material_pk']
        mic = MaterialInCasestudy.objects.get(id=material_pk)

        obj = self.Meta.model.objects.create(
            material=mic,
            **validated_data)
        return obj


class ActivitySetField(InCasestudyField):
    lookup_url_kwarg = 'activitygroup_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'activitygroup__casestudy__id',
                            'activitygroup_pk': 'activitygroup__id', }


class ActivityListField(IdentityFieldMixin, ActivitySetField):
    """"""
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id',
                            'activitygroup_pk': 'id', }


class ActivityGroupSerializer(CreateWithUserInCasestudyMixin,
                               NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    activity_list = ActivityListField(
        source='activity_set',
        view_name='activity-list')
    activity_set = ActivitySetField(many=True,
                                    view_name='activity-detail',
                                    read_only=True)
    inputs = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    outputs = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    stocks = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    class Meta:
        model = ActivityGroup
        fields = ('url', 'id', 'code', 'name', 'activity_set', 'activity_list',
                  'inputs', 'outputs', 'stocks')


class ActivityGroupField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}


class ActorSetField(InCasestudyField):
    lookup_url_kwarg = 'activity_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'activity__activitygroup__casestudy__id',
                            'activitygroup_pk': 'activity__activitygroup__id',
                            'activity_pk': 'activity__id',}


class ActorListField(IdentityFieldMixin, ActorSetField):
    """"""
    parent_lookup_kwargs = {'casestudy_pk': 'activitygroup__casestudy__id',
                            'activitygroup_pk': 'activitygroup__id',
                            'activity_pk': 'id',}


class ActivitySerializer(CreateWithUserInCasestudyMixin,
                         NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'activitygroup__casestudy__id',
        'activitygroup_pk': 'activitygroup__id',
    }
    activitygroup = IDRelatedField()
    activitygroup_url = ActivityGroupField(view_name='activitygroup-detail',
                                           source='activitygroup',
                                           read_only=True)
    actor_list = ActorListField(source='actor_set',
                                view_name='actor-list')
    actor_set = ActorSetField(many=True,
                              view_name='actor-detail',
                              read_only=True)
    class Meta:
        model = Activity
        fields = ('url', 'id', 'nace', 'name', 'activitygroup',
                  'activitygroup_url', 'actor_set',
                  'actor_list')


class AllActivitySerializer(ActivitySerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'activitygroup__casestudy__id'}


class ActivityField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'activitygroup__casestudy__id',
                            'activitygroup_pk': 'activitygroup__id',}


class ActorSerializer(CreateWithUserInCasestudyMixin,
                      NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'activity__activitygroup__casestudy__id',
        'activitygroup_pk': 'activity__activitygroup__id',
        'activity_pk': 'activity__id',
    }
    activity = IDRelatedField()
    activity_url = ActivityField(view_name='activity-detail',
                                 source='activity',
                                 read_only=True)
    class Meta:
        model = Actor
        fields = ('url', 'id', 'BvDid', 'name', 'consCode', 'year', 'revenue',
                  'employees', 'BvDii', 'website', 'activity', 'activity_url')


class AllActorSerializer(ActorSerializer):
    parent_lookup_kwargs = {'casestudy_pk':
                            'activity__activitygroup__casestudy__id'}


class ActorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ('BvDid', 'name', 'activity')


class MaterialInCasestudyField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id',
                            }


class StockSerializer(MaterialInCasestudyDetailCreateMixin,
                      NestedHyperlinkedModelSerializer):
    material = MaterialInCasestudyField(view_name='materialincasestudy-detail',
                                        read_only=True)
    parent_lookup_kwargs = {
        'casestudy_pk': 'material__casestudy__id',
        'material_pk': 'material__id',
    }
    class Meta:
        model = Stock
        fields = ('url', 'id', 'origin', 'amount', 'quality',
                  'material',
                  )


class GroupStockSerializer(StockSerializer):
    origin = ActivityGroupField(view_name='activitygroup-detail')
    class Meta(StockSerializer.Meta):
        model = GroupStock


class ActivityStockSerializer(StockSerializer):
    origin = ActivityField(view_name='activity-detail')
    class Meta(StockSerializer.Meta):
        model = ActivityStock


class ActorField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'activity__activitygroup__casestudy__id',
                            'activitygroup_pk': 'activity__activitygroup__id',
                            'activity_pk': 'activity__id',}


class ActorStockSerializer(StockSerializer):
    origin = ActorField(view_name='actor-detail')
    class Meta(StockSerializer.Meta):
        model = ActorStock


class FlowSerializer(MaterialInCasestudyDetailCreateMixin,
                     NestedHyperlinkedModelSerializer):
    """Abstract Base Class for a Flow Serializer"""
    parent_lookup_kwargs = {
        'casestudy_pk': 'material__casestudy__id',
        'material_pk': 'material__id',
    }
    material = MaterialInCasestudyField(view_name='materialincasestudy-detail',
                                        read_only=True)

    class Meta:
        model = Flow
        fields = ('url', 'id',
                  'material',
                  'amount', 'quality', 'origin',
                  'destination')


class Group2GroupSerializer(FlowSerializer):
    origin = IDRelatedField()
    origin_url = ActivityGroupField(view_name='activitygroup-detail',
                                    source='origin',
                                    read_only=True)
    destination = IDRelatedField()
    destination_url = ActivityGroupField(view_name='activitygroup-detail',
                                         source='destination',
                                         read_only=True)
    quality = IDRelatedField()
    
    class Meta(FlowSerializer.Meta):
        model = Group2Group
        fields = ('id', 'amount', 'quality', 'material', 'origin', 'origin_url',
                  'destination', 'destination_url')


class Activity2ActivitySerializer(FlowSerializer):
    origin = IDRelatedField()
    origin_url = ActivityField(view_name='activity-detail',
                                source='origin',
                                read_only=True)
    destination = IDRelatedField()
    destination_url = ActivityField(view_name='activity-detail',
                                    source='destination',
                                    read_only=True)
    quality = IDRelatedField()

    class Meta(FlowSerializer.Meta):
        model = Activity2Activity
        fields = ('id', 'amount', 'quality', 'material', 'origin', 'origin_url',
                  'destination', 'destination_url')


class Actor2ActorSerializer(FlowSerializer):
    origin = IDRelatedField()
    origin_url = ActorField(view_name='actor-detail',
                            source='origin',
                            read_only=True)
    destination = IDRelatedField()
    destination_url = ActorField(view_name='actor-detail',
                                 source='destination',
                                 read_only=True)
    quality = IDRelatedField()

    class Meta(FlowSerializer.Meta):
        model = Actor2Actor
        fields = ('id', 'amount', 'quality', 'material', 'origin', 'origin_url',
                  'destination', 'destination_url')


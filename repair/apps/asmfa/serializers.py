from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from repair.apps.login.models import CaseStudy
from repair.apps.asmfa.models import (ActivityGroup,
                                      Activity,
                                      Actor,
                                      Flow,
                                      Stock,
                                      Actor2Actor,
                                      Activity2Activity,
                                      Group2Group,
                                      Keyflow,
                                      Quality,
                                      KeyflowInCasestudy,
                                      GroupStock,
                                      ActivityStock,
                                      ActorStock,
                                      Geolocation,
                                      OperationalLocationOfActor,
                                      )

from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           InCasestudyField,
                                           InCaseStudyIdentityField,
                                           InCasestudyListField,
                                           IdentityFieldMixin,
                                           CreateWithUserInCasestudyMixin,
                                           NestedHyperlinkedRelatedField,
                                           IDRelatedField)


class KeyflowSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    casestudies = serializers.HyperlinkedRelatedField(
        queryset = CaseStudy.objects,
        many=True,
        view_name='casestudy-detail',
        help_text=_('Select the Casestudies the Keyflow is used in')
    )

    class Meta:
        model = Keyflow
        fields = ('url', 'id', 'code', 'name', 'casestudies')


    def update(self, obj, validated_data):
        """update the user-attributes, including profile information"""
        Keyflow = obj

        # handle groups
        new_casestudies = validated_data.pop('casestudies', None)
        if new_casestudies is not None:
            KeyflowInCasestudy = Keyflow.casestudies.through
            casestudy_qs = KeyflowInCasestudy.objects.filter(
                Keyflow=Keyflow.id)
            # delete existing groups
            casestudy_qs.exclude(
                casestudy__id__in=(cs.id for cs in new_casestudies)).delete()
            # add or update new groups
            for cs in new_casestudies:
                KeyflowInCasestudy.objects.update_or_create(Keyflow=Keyflow,
                                                             casestudy=cs)

        # update other attributes
        for attr, value in validated_data.items():
            setattr(obj, attr, value)
        obj.save()
        return obj

    def create(self, validated_data):
        """Create a new Keyflow"""
        code = validated_data.pop('code')

        Keyflow = Keyflow.objects.create(code=code)
        self.update(obj=Keyflow, validated_data=validated_data)
        return Keyflow


class QualitySerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}

    class Meta:
        model = Quality
        fields = ('url', 'id', 'name')

class InKeyflowField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk':
        'Keyflow__casestudy__id',
        'Keyflow_pk': 'Keyflow__id',}
    extra_lookup_kwargs = {}
    filter_field = 'Keyflow_pk'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.casestudy_pk_lookup['Keyflow_pk'] = \
            self.parent_lookup_kwargs['Keyflow_pk']


class InKeyflowSetField(IdentityFieldMixin, InKeyflowField, ):
    """Field that returns a list of all items in the casestudy"""
    lookup_url_kwarg = 'Keyflow_pk'
    parent_lookup_kwargs = {
        'casestudy_pk':
        'casestudy__id',
        'Keyflow_pk': 'id',}


class KeyflowField(NestedHyperlinkedRelatedField):
    parent_lookup_kwargs = {'pk': 'id'}
    queryset = Keyflow.objects
    """This is fixed in rest_framework_nested, but not yet available on pypi"""
    def use_pk_only_optimization(self):
        return False


class KeyflowInCasestudySerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    note = serializers.CharField(required=False, allow_blank=True)
    Keyflow = KeyflowField(
        view_name='Keyflow-detail',
    )
    groupstock_set = InKeyflowSetField(view_name='groupstock-list')
    group2group_set = InKeyflowSetField(view_name='group2group-list')
    activitystock_set = InKeyflowSetField(view_name='activitystock-list')
    activity2activity_set = InKeyflowSetField(view_name='activity2activity-list')
    actorstock_set = InKeyflowSetField(view_name='actorstock-list')
    actor2actor_set = InKeyflowSetField(view_name='actor2actor-list')

    class Meta:
        model = KeyflowInCasestudy
        fields = ('url',
                  'id',
                  'Keyflow',
                  'note',
                  'groupstock_set',
                  'group2group_set',
                  'activitystock_set',
                  'activity2activity_set',
                  'actorstock_set',
                  'actor2actor_set')


class KeyflowInCasestudyDetailCreateMixin:
    def create(self, validated_data):
        """Create a new solution quantity"""
        # Note by Christoph: why is the keyflow_pk in session['casestudy_pk']
        # alongside with the key casestudy_pk?
        # is it supposed to be this way?
        casestudy_session = self.context['request'].session['casestudy_pk']
        casestudy_pk = casestudy_session['casestudy_pk']
        Keyflow_pk = self.context['request'].session['Keyflow_pk']
        # ToDo: raise some kind of exception or prevent creating object with
        # wrong keyflow/casestudy combination somewhere else (view.update?)
        # atm the server will just hang up here
        mic = KeyflowInCasestudy.objects.get(id=keyflow_pk,

        obj = self.Meta.model.objects.create(
            Keyflow=mic,
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


class GeolocationInCasestudyField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}


class GeolocationInCasestudySetField(InCasestudyField):
    lookup_url_kwarg = 'casestudy_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}


class GeolocationInCasestudyListField(IdentityFieldMixin,
                                      GeolocationInCasestudySetField):
    """"""
    parent_lookup_kwargs = {'casestudy_pk':
                            'activity__activitygroup__casestudy__id'}


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
                  'employees', 'BvDii', 'website', 'activity', 'activity_url',
                  'included',
                  'administrative_location',
                  )

    def update(self, obj, validated_data):
        """
        update the operation locations,
        including selected solutions
        """
        actor = obj
        actor_id = actor.id

        # handle operational locations
        new_op_locations = validated_data.pop('operational_locations', None)
        if new_op_locations is not None:
            ThroughModel = Actor.operational_locations.through
            locations_qs = ThroughModel.objects.filter(
                actor=actor)
            # delete existing locations
            locations_qs.exclude(location_id__in=(
                loc.id for loc in new_op_locations)).delete()
            # add or update new locations
            for loc in new_op_locations:
                ThroughModel.objects.update_or_create(
                    actor=actor,
                    location=loc)

        # update other attributes
        for attr, value in validated_data.items():
            setattr(obj, attr, value)
        obj.save()
        return obj


class GeolocationInCasestudySet2Field(InCasestudyField):
    lookup_url_kwarg = 'casestudy_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id',}


class GeolocationInCasestudy2ListField(IdentityFieldMixin,
                                      GeolocationInCasestudySet2Field):
    """"""
    parent_lookup_kwargs = {'casestudy_pk':
                            'activity__activitygroup__casestudy__id',
                            'actor_pk': 'id',}


class AllActorSerializer(ActorSerializer):
    parent_lookup_kwargs = {'casestudy_pk':
                            'activity__activitygroup__casestudy__id'}

    administrative_location_url = GeolocationInCasestudyField(
        view_name='geolocation-detail',
        source='administrative_location')


    operational_location_list = GeolocationInCasestudy2ListField(
        source='operational_locations',
        view_name='operationallocationofactor-list',
        read_only=True)

    operational_location_set = GeolocationInCasestudySet2Field(
        source='operational_locations',
        many=True,
        view_name='geolocation-detail')

    class Meta:
        model = Actor
        fields = ('url', 'id', 'BvDid', 'name', 'consCode', 'year', 'revenue',
                  'employees', 'BvDii', 'website', 'activity', 'activity_url',
                  'included',
                  'administrative_location_url',
                  'operational_location_set',
                  'operational_location_list',
                  )


class LocationField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}


class Actor2Field(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk':
                            'activity__activitygroup__casestudy__id'}


class OperationalLocationOfActorSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'location__casestudy__id',
        'actor_pk': 'actor__id',
    }
    actor = Actor2Field(view_name='actor-detail')
    location = LocationField(view_name='geolocation-detail')
    class Meta:
        model = OperationalLocationOfActor
        fields = ('url', 'id', 'actor', 'location', 'note')



class ActorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ('BvDid', 'name', 'activity')


class KeyflowInCasestudyField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id',
                            }


class StockSerializer(KeyflowInCasestudyDetailCreateMixin,
                           NestedHyperlinkedModelSerializer):
    Keyflow = KeyflowInCasestudyField(view_name='Keyflowincasestudy-detail',
                                        read_only=True)
    parent_lookup_kwargs = {
        'casestudy_pk': 'Keyflow__casestudy__id',
        'Keyflow_pk': 'Keyflow__id',
    }
    class Meta:
        model = Stock
        fields = ('url', 'id', 'origin', 'amount', 'quality',
                  'Keyflow',
                  )


class GroupStockSerializer(StockSerializer):
    origin = IDRelatedField()
    quality = IDRelatedField()
    #origin_url = ActivityGroupField(view_name='activitygroup-detail')

    class Meta(StockSerializer.Meta):
        model = GroupStock


class ActivityStockSerializer(StockSerializer):
    origin = IDRelatedField()
    quality = IDRelatedField()
    #origin_url = ActivityField(view_name='activity-detail')
    class Meta(StockSerializer.Meta):
        model = ActivityStock


class ActorField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'activity__activitygroup__casestudy__id',
                            'activitygroup_pk': 'activity__activitygroup__id',
                            'activity_pk': 'activity__id',}


class ActorStockSerializer(StockSerializer):
    origin = IDRelatedField()
    quality = IDRelatedField()
    #origin_url = ActorField(view_name='actor-detail')
    class Meta(StockSerializer.Meta):
        model = ActorStock


class FlowSerializer(KeyflowInCasestudyDetailCreateMixin,
                     NestedHyperlinkedModelSerializer):
    """Abstract Base Class for a Flow Serializer"""
    parent_lookup_kwargs = {
        'casestudy_pk': 'Keyflow__casestudy__id',
        'Keyflow_pk': 'Keyflow__id',
    }
    Keyflow = KeyflowInCasestudyField(view_name='Keyflowincasestudy-detail',
                                        read_only=True)

    class Meta:
        model = Flow
        fields = ('url', 'id',
                  'Keyflow',
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
        fields = ('id', 'amount', 'quality', 'keyflow', 'origin', 'origin_url',
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
        fields = ('id', 'amount', 'quality', 'keyflow', 'origin', 'origin_url',
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
        fields = ('id', 'amount', 'quality', 'keyflow', 'origin', 'origin_url',
                  'destination', 'destination_url')


class GeolocationSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}

    class Meta:
        model = Geolocation
        fields = ('url', 'id', 'casestudy', 'geom', 'street')


class ActorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ('BvDid', 'name', 'activity')

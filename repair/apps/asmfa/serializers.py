from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _
from django.core.validators import URLValidator
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError

from rest_framework_gis.serializers import (GeoFeatureModelSerializer)

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
                                      KeyflowInCasestudy,
                                      GroupStock,
                                      ActivityStock,
                                      ActorStock,
                                      AdministrativeLocation,
                                      OperationalLocation,
                                      Product,
                                      ProductFraction,
                                      Material,
                                     )

from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           InCasestudyField,
                                           InCasestudyListField,
                                           IdentityFieldMixin,
                                           CreateWithUserInCasestudyMixin,
                                           NestedHyperlinkedRelatedField,
                                           IDRelatedField,
                                           CasestudyField)


class InCasestudyKeyflowListField(InCasestudyListField):
    """Field that returns a list of all items in the keyflow in the casestudy"""
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
        'keyflow_pk': 'keyflow__id',}
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
        'keyflow_pk': 'id',}


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
    keyflow = KeyflowField(view_name='keyflow-detail')
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


class KeyflowInCasestudyPostSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    note = serializers.CharField(required=False, allow_blank=True)
    keyflow = KeyflowField(view_name='keyflow-detail')
    #casestudy = CasestudyField(view_name='casestudy-detail')

    class Meta:
        model = KeyflowInCasestudy
        fields = ('keyflow',
                  'note',
                  )

    def get_casestudy(self):
        url_pks = self.context['request'].session['url_pks']
        casestudy_pk = url_pks['casestudy_pk']
        casestudy = CaseStudy.objects.get(id=casestudy_pk)
        return casestudy

    def create(self, validated_data):
        """Create a new keyflow in casestury"""
        casestudy = self.get_casestudy()
        obj = self.Meta.model.objects.create(
            casestudy=casestudy,
            **validated_data)
        return obj

    def update(self, obj, validated_data):
        casestudy = self.get_casestudy()
        validated_data['casestudy'] = casestudy
        return super().update(obj, validated_data)


class KeyflowInCasestudyDetailCreateMixin:
    def create(self, validated_data):
        """Create a new solution quantity"""
        url_pks = self.context['request'].session['url_pks']
        #casestudy_pk = url_pks['casestudy_pk']
        keyflow_pk = url_pks['keyflow_pk']
        # ToDo: raise some kind of exception or prevent creating object with
        # wrong keyflow/casestudy combination somewhere else (view.update?)
        # atm the server will just hang up here
        mic = KeyflowInCasestudy.objects.get(id=keyflow_pk)
        validated_data['keyflow'] = mic

        obj = self.Meta.model.objects.create(
            **validated_data)
        return obj


class ActivitySetField(InCasestudyField):
    lookup_url_kwarg = 'activitygroup_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'activitygroup__keyflow__casestudy__id',
                            'keyflow_pk': 'activitygroup__keyflow__id',
                            'activitygroup_pk': 'activitygroup__id', }


class ActivityListField(IdentityFieldMixin, ActivitySetField):
    """"""
    parent_lookup_kwargs = {'casestudy_pk': 'keyflow__casestudy__id',
                            'keyflow_pk': 'keyflow__id',
                            'activitygroup_pk': 'id', }


class ActivityGroupSerializer(CreateWithUserInCasestudyMixin,
                              NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'keyflow__casestudy__id',
                            'keyflow_pk': 'keyflow__id',}
    activity_list = ActivityListField(
        source='activity_set',
        view_name='activity-list')
    activity_set = ActivitySetField(many=True,
                                    view_name='activity-detail',
                                    read_only=True)
    inputs = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    outputs = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    stocks = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    keyflow = IDRelatedField(required=False)
    class Meta:
        model = ActivityGroup
        fields = ('url', 'id', 'code', 'name', 'activity_set', 'activity_list',
                  'inputs', 'outputs', 'stocks', 'keyflow')


class ActivityGroupField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'keyflow__casestudy__id',
                            'keyflow_pk': 'keyflow__id',}


class ActorSetField(InCasestudyField):
    lookup_url_kwarg = 'activity_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'activity__activitygroup__keyflow__casestudy__id',
                            'keyflow_pk': 'activity__activitygroup__keyflow__id',
                            'activitygroup_pk': 'activity__activitygroup__id',
                            'activity_pk': 'activity__id',}


class ActorListField(IdentityFieldMixin, ActorSetField):
    """"""
    parent_lookup_kwargs = {'casestudy_pk': 'activitygroup__keyflow__casestudy__id',
                            'keyflow_pk': 'activitygroup__keyflow__id',
                            'activitygroup_pk': 'activitygroup__id',
                            'activity_pk': 'id',}


class ActivitySerializer(CreateWithUserInCasestudyMixin,
                         NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'activitygroup__keyflow__casestudy__id',
        'keyflow_pk': 'activitygroup__keyflow__id',
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
    parent_lookup_kwargs = {'casestudy_pk':
                            'activitygroup__keyflow__casestudy__id',
                            'keyflow_pk': 'activitygroup__keyflow__id',}


class ActivityField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk':
                            'activitygroup__keyflow__casestudy__id',
                            'keyflow_pk': 'activitygroup__keyflow__id',
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
                            'activity__activitygroup__keyflow__casestudy__id'}


class GeolocationInCasestudySet2Field(InCasestudyField):
    lookup_url_kwarg = 'casestudy_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id',}


class GeolocationInCasestudy2ListField(IdentityFieldMixin,
                                       GeolocationInCasestudySet2Field):
    """"""
    parent_lookup_kwargs = {'casestudy_pk':
                            'activity__activitygroup__keyflow__casestudy__id',
                            'actor_pk': 'id',}


class AdminLocationGeojsonField(GeoFeatureModelSerializer):
    actor = serializers.PrimaryKeyRelatedField(queryset=Actor.objects.all())
    class Meta:
        model = AdministrativeLocation
        geo_field = 'geom'
        fields = ['id', 'address', 'postcode', 'country',
                  'city', 'name', 'actor']


class OperationsLocationsGeojsonField(GeoFeatureModelSerializer):
    actor = serializers.PrimaryKeyRelatedField(queryset=Actor.objects.all())
    id = serializers.IntegerField(label='ID')

    class Meta:
        model = OperationalLocation
        geo_field = 'geom'
        fields = ['id', 'address', 'postcode', 'country',
                  'city', 'name', 'actor']

class URLWithoutProtocolValidator(URLValidator):
    def __call__(self, value):
        if len(value.split('://')) < 2:
            value = 'http://{}'.format(value)
        return super().__call__(value)


class URLFieldWithoutProtocol(serializers.CharField):
    default_error_messages = {'invalid': _('Enter a valid URL (or leave it blank).')}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # add new validator
        validator = URLWithoutProtocolValidator(
            message=self.error_messages['invalid'])
        self.validators.append(validator)


class ActorSerializer(CreateWithUserInCasestudyMixin,
                      NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'activity__activitygroup__keyflow__casestudy__id',
        'keyflow_pk': 'activity__activitygroup__keyflow__id',
        'activitygroup_pk': 'activity__activitygroup__id',
        'activity_pk': 'activity__id',
    }
    activity = IDRelatedField()
    activity_url = ActivityField(view_name='activity-detail',
                                 source='activity',
                                 read_only=True)

    #administrative_location_geojson = AdminLocationGeojsonField(
        #source='administrative_location',
        #required=False,
    #)

    #operational_locations_geojson = OperationsLocationsGeojsonField(
        #source='operational_locations',
        #many=True,
        #required=False,
    #)
    website = URLFieldWithoutProtocol(required=False, default="", allow_blank=True)

    class Meta:
        model = Actor
        fields = ('url', 'id', 'BvDid', 'name', 'consCode', 'year', 'turnover',
                  'employees', 'BvDii', 'website', 'activity', 'activity_url',
                  'included',
                  'reason',
                  #'administrative_location_geojson',
                  #'operational_locations_geojson',
                 )


    #def update(self, obj, validated_data):
        #"""update the user-attributes, including profile information"""
        #actor = obj

        ## handle administrative location
        #administrative_location = validated_data.pop('administrative_location',
                                                     #None)
        #if administrative_location is not None:
            ### get the actor from the request or take the obj
            ##actor = administrative_location.pop('actor', obj)
            ## look if actor has already an administrative location
            #aloc = AdministrativeLocation.objects.get_or_create(actor=actor)[0]
            #for attr, value in administrative_location.items():
                #if attr == 'actor':
                    #continue
                #setattr(aloc, attr, value)
            #aloc.save()
            ##obj.administrativelocation = aloc

        ## handle operational locations
        #operational_locations = validated_data.pop('operational_locations',
                                                   #None)
        #if operational_locations is not None:
            #olocs = OperationalLocation.objects.filter(actor=actor)
            ## delete existing rows not needed any more
            #to_delete = olocs.exclude(id__in=(ol.get('id') for ol
                                              #in operational_locations
                                              #if ol.get('id') is not None))
            #to_delete.delete()
            ## add or update new operational locations
            #for operational_location in operational_locations:
                #oloc = OperationalLocation.objects.update_or_create(
                    #actor=actor, id=operational_location.get('id'))[0]


                #for attr, value in operational_location.items():
                    #if attr == 'actor':
                        #continue
                    #setattr(oloc, attr, value)
                #oloc.save()

        ## update other attributes
        #for attr, value in validated_data.items():
            #setattr(obj, attr, value)
        #obj.save()
        #return obj


class AllActorSerializer(ActorSerializer):
    parent_lookup_kwargs = {'casestudy_pk':
                            'activity__activitygroup__keyflow__casestudy__id',
                            'keyflow_pk':
                            'activity__activitygroup__keyflow__id',}


class AllActorListSerializer(AllActorSerializer):
    class Meta(AllActorSerializer.Meta):
        fields = ('url', 'id', 'BvDid', 'name', 'consCode', 'year', 'turnover',
                  'employees', 'BvDii', 'website', 'activity', 'activity_url',
                  'included', 'reason', )


class LocationField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}


class KeyflowInCasestudyField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id',
                            }


class ProductInKeyflowInCasestudyField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }

class StockSerializer(KeyflowInCasestudyDetailCreateMixin,
                      NestedHyperlinkedModelSerializer):
    keyflow = KeyflowInCasestudyField(view_name='keyflowincasestudy-detail',
                                      read_only=True)
    product = IDRelatedField()

    #product = ProductInKeyflowInCasestudyField(view_name='product-detail')
    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }
    class Meta:
        model = Stock
        fields = ('url', 'id', 'origin', 'amount',
                  'keyflow', 'year', 'product',
                  )


class GroupStockSerializer(StockSerializer):
    origin = IDRelatedField()
    #origin_url = ActivityGroupField(view_name='activitygroup-detail')

    class Meta(StockSerializer.Meta):
        model = GroupStock


class ActivityStockSerializer(StockSerializer):
    origin = IDRelatedField()
    #origin_url = ActivityField(view_name='activity-detail')
    class Meta(StockSerializer.Meta):
        model = ActivityStock


class ActorField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'activity__activitygroup__keyflow__casestudy__id',
        'keyflow_pk': 'activity__activitygroup__keyflow__id',
        'activitygroup_pk': 'activity__activitygroup__id',
        'activity_pk': 'activity__id',}


class ActorStockSerializer(StockSerializer):
    origin = IDRelatedField()

    class Meta(StockSerializer.Meta):
        model = ActorStock


class FlowSerializer(KeyflowInCasestudyDetailCreateMixin,
                     NestedHyperlinkedModelSerializer):
    """Abstract Base Class for a Flow Serializer"""
    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }
    keyflow = KeyflowInCasestudyField(view_name='keyflowincasestudy-detail',
                                        read_only=True)

    class Meta:
        model = Flow
        fields = ('url', 'id',
                  'keyflow',
                  'amount', 'origin',
                  'destination', 'product', 'description', 'year')


class Group2GroupSerializer(FlowSerializer):
    origin = IDRelatedField()
    origin_url = ActivityGroupField(view_name='activitygroup-detail',
                                    source='origin',
                                    read_only=True)
    product = IDRelatedField()
    destination = IDRelatedField()
    destination_url = ActivityGroupField(view_name='activitygroup-detail',
                                         source='destination',
                                         read_only=True)
    #quality = IDRelatedField()

    class Meta(FlowSerializer.Meta):
        model = Group2Group
        fields = ('id', 'amount', 'keyflow', 'origin', 'origin_url',
                  'destination', 'destination_url', 'product', 'description',
                  'year')


class Activity2ActivitySerializer(FlowSerializer):
    origin = IDRelatedField()
    origin_url = ActivityField(view_name='activity-detail',
                                source='origin',
                                read_only=True)
    product = IDRelatedField()
    destination = IDRelatedField()
    destination_url = ActivityField(view_name='activity-detail',
                                    source='destination',
                                    read_only=True)
    #quality = IDRelatedField()

    class Meta(FlowSerializer.Meta):
        model = Activity2Activity
        fields = ('id', 'amount', 'keyflow', 'origin', 'origin_url',
                  'destination', 'destination_url', 'product', 'description',
                  'year')


class Actor2ActorSerializer(FlowSerializer):
    origin = IDRelatedField()
    origin_url = ActorField(view_name='actor-detail',
                            source='origin',
                            read_only=True)
    product = IDRelatedField()
    destination = IDRelatedField()
    destination_url = ActorField(view_name='actor-detail',
                                 source='destination',
                                 read_only=True)

    class Meta(FlowSerializer.Meta):
        model = Actor2Actor
        fields = ('id', 'amount', 'keyflow',
                  'origin', 'origin_url',
                  'destination', 'destination_url', 'product', 'description',
                  'year')


class AllActorField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk':
                            'activity__activitygroup__keyflow__casestudy__id',
                            'keyflow_pk':
                            'activity__activitygroup__keyflow__id',}


class ActorIDField(serializers.RelatedField):
    """"""
    default_error_messages = {
        'required': _('This field is required.'),
        'does_not_exist': _('Invalid Actor ID - Object does not exist.'),
        'null': _('This field may not be null.')
    }


    def to_representation(self, value):
        return value.id

    def to_internal_value(self, data):
        try:
            return Actor.objects.get(id=data)
        except (ObjectDoesNotExist, TypeError, ValueError):
            self.fail('does_not_exist')

    def get_queryset(self):
        qs = Actor.objects.all()
        return qs


class PatchFields:

    @property
    def fields(self):
        fields = super().fields
        for fn in ['type', 'geometry', 'properties']:
            if not fn in fields:
                fields[fn] = serializers.CharField(write_only=True,
                                                   required=False)
        return fields

    #def create(self, validated_data, **kwargs):
        #"""
        #"""
        #obj = self.Meta.model(**kwargs)
        #self._for_write = True
        #obj.save(force_insert=True, using=self.db)
        #return obj


class AdministrativeLocationSerializer(PatchFields,
                                       GeoFeatureModelSerializer,
                                       NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk':
                            'actor__activity__activitygroup__keyflow__casestudy__id',
                            'keyflow_pk':
                            'actor__activity__activitygroup__keyflow__id',}
    actor = ActorIDField()
    class Meta:
        model = AdministrativeLocation
        geo_field = 'geom'
        fields = ['id', 'url', 'address', 'postcode', 'country',
                  'city', 'geom', 'name',
                  'actor',
                  ]

    def create(self, validated_data):
        """Create a new AdministrativeLocation"""
        if self.Meta.model.objects.all().filter(actor = validated_data['actor']):
            msg = _('Actor <{}> already has an administrative location (has to be unique).'
                    .format(validated_data['actor']))
            raise ValidationError(detail=msg)
        return super().create(validated_data)


class AdministrativeLocationOfActorSerializer(AdministrativeLocationSerializer):
    parent_lookup_kwargs = {'casestudy_pk':
                            'actor__activity__activitygroup__keyflow__casestudy__id',
                            'keyflow_pk':
                            'actor__activity__activitygroup__keyflow__id',
                            'actor_pk': 'actor__id',}
    actor = ActorIDField(required=False)

    def create(self, validated_data):
        """Create a new AdministrativeLocation"""
        actor = validated_data.pop('actor', None)
        if actor is None:
            url_pks = self.context['request'].session['url_pks']
            actor_pk = url_pks['actor_pk']
            actor = Actor.objects.get(pk=actor_pk)

        aloc = AdministrativeLocation.objects.get_or_create(actor=actor)[0]
        for attr, value in validated_data.items():
            setattr(aloc, attr, value)
        aloc.save()
        return aloc


class AdministrativeLocationOfActorPostSerializer(AdministrativeLocationOfActorSerializer):
    class Meta:
        model = AdministrativeLocation
        geo_field = 'geom'
        fields = ['id', 'url', 'address', 'postcode', 'country',
                  'city', 'geom', 'name',
                  ]


class OperationalLocationSerializer(PatchFields,
                                    GeoFeatureModelSerializer,
                                    NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk':
                            'actor__activity__activitygroup__keyflow__casestudy__id',
                            'keyflow_pk':
                            'actor__activity__activitygroup__keyflow__id',}
    actor = ActorIDField()

    class Meta:
        model = OperationalLocation
        geo_field = 'geom'
        fields = ['id', 'url', 'address', 'postcode', 'country',
                  'city', 'geom', 'name', 'actor']


class OperationalLocationsOfActorSerializer(OperationalLocationSerializer):
    parent_lookup_kwargs = {'casestudy_pk':
                            'actor__activity__activitygroup__keyflow__casestudy__id',
                            'keyflow_pk':
                            'actor__activity__activitygroup__keyflow__id',
                            'actor_pk': 'actor__id',}
    id = serializers.IntegerField(label='ID', required=False)
    actor = ActorIDField(required=False)

    def create(self, validated_data):
        """Handle Post on OperationalLocations"""
        url_pks = self.context['request'].session['url_pks']
        actor_pk = url_pks['actor_pk']
        actor = Actor.objects.get(pk=actor_pk)

        operational_locations = validated_data.get('features', None)

        if operational_locations is None:
            # No Feature Collection: Add Single Location
            validated_data['actor'] = actor
            return super().create(validated_data)
        else:
            # Feature Collection: Add all Locations
            olocs = OperationalLocation.objects.filter(actor=actor)
            # delete existing rows not needed any more
            to_delete = olocs.exclude(id__in=(ol.get('id') for ol
                                              in operational_locations
                                              if ol.get('id') is not None))
            to_delete.delete()
            # add or update new operational locations
            for operational_location in operational_locations:
                oloc = OperationalLocation.objects.update_or_create(
                    actor=actor, id=operational_location.get('id'))[0]


                for attr, value in operational_location.items():
                    setattr(oloc, attr, value)
                oloc.save()

        # return the last location that was created
        return oloc

    def to_internal_value(self, data):
        """
        Override the parent method to parse all features and
        remove the GeoJSON formatting
        """
        if data.get('type') == 'FeatureCollection':
            internal_data_list = list()
            for feature in data.get('features', []):
                if 'properties' in data:
                    feature = self.unformat_geojson(feature)
                internal_data = super().to_internal_value(feature)
                internal_data_list.append(internal_data)

            return {'features': internal_data_list}
        return super().to_internal_value(data)


class ProductFractionSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductFraction
        fields = ('id',
                  'product',
                  'material',
                  'fraction')
        read_only_fields = ['id', 'product']


class ProductSerializer(KeyflowInCasestudyDetailCreateMixin,
                        NestedHyperlinkedModelSerializer):
    keyflow = KeyflowInCasestudyField(view_name='keyflowincasestudy-detail',
                                      read_only=True)
    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }
    fractions = ProductFractionSerializer(many=True)

    class Meta:
        model = Product
        fields = ('url', 'id', 'name', 'default',
                  'keyflow',
                  'fractions',
                  )

    def create(self, validated_data):
        fractions = validated_data.pop('fractions')
        obj = super().create(validated_data)
        validated_data['fractions'] = fractions
        self.update(obj, validated_data)
        return obj

    def update(self, obj, validated_data):
        """update the user-attributes, including fraction information"""
        product = obj

        # handle product fractions
        new_fractions = validated_data.pop('fractions', None)

        if new_fractions is not None:
            product_fractions = ProductFraction.objects.filter(product=product)
            # delete existing rows not needed any more
            to_delete = product_fractions.exclude(
                material__id__in=(getattr(fraction.get('material'), 'id') for fraction
                        in new_fractions
                        if getattr(fraction.get('material'), 'id') is not None))
            to_delete.delete()
            # add or update new fractions
            for new_fraction in new_fractions:
                material_id = getattr(new_fraction.get('material'), 'id')
                material = Material.objects.get(id=material_id)
                #fraction = ProductFraction.objects.get(product=product,
                                                       #material__id=material_id)
                fraction = ProductFraction.objects.update_or_create(
                    product=product,
                    material=material)[0]


                for attr, value in new_fraction.items():
                    if attr in ('product', 'material'):
                        continue
                    setattr(fraction, attr, value)
                fraction.save()

        # update other attributes
        for attr, value in validated_data.items():
            setattr(obj, attr, value)
        obj.save()
        return obj


class MaterialSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}

    class Meta:
        model = Material
        fields = ('url', 'id', 'name', 'code', 'flowType')
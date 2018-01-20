
from django.utils.translation import ugettext_lazy as _
from django.core.validators import URLValidator
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from repair.apps.asmfa.models import (ActivityGroup,
                                      Activity,
                                      Actor,
                                      AdministrativeLocation,
                                      OperationalLocation,
                                     )

from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           InCasestudyField,
                                           IdentityFieldMixin,
                                           CreateWithUserInCasestudyMixin,
                                           IDRelatedField)


class ActivitySetField(InCasestudyField):
    lookup_url_kwarg = 'activitygroup_pk'
    parent_lookup_kwargs = {'casestudy_pk':
                            'activitygroup__keyflow__casestudy__id',
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


class ActorField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'activity__activitygroup__keyflow__casestudy__id',
        'keyflow_pk': 'activity__activitygroup__keyflow__id',
        'activitygroup_pk': 'activity__activitygroup__id',
        'activity_pk': 'activity__id',}


class ActorSetField(InCasestudyField):
    lookup_url_kwarg = 'activity_pk'
    parent_lookup_kwargs = {
        'casestudy_pk': 'activity__activitygroup__keyflow__casestudy__id',
        'keyflow_pk': 'activity__activitygroup__keyflow__id',
        'activitygroup_pk': 'activity__activitygroup__id',
        'activity_pk': 'activity__id',}


class ActorListField(IdentityFieldMixin, ActorSetField):
    """"""
    parent_lookup_kwargs = {'casestudy_pk': 'activitygroup__keyflow__casestudy__id',
                            'keyflow_pk': 'activitygroup__keyflow__id',
                            'activitygroup_pk': 'activitygroup__id',
                            'activity_pk': 'id',}


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
    default_error_messages = {'invalid':
                              _('Enter a valid URL (or leave it blank).')}

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

    website = URLFieldWithoutProtocol(required=False, default="",
                                      allow_blank=True)

    class Meta:
        model = Actor
        fields = ('url', 'id', 'BvDid', 'name', 'consCode', 'year', 'turnover',
                  'employees', 'BvDii', 'website', 'activity', 'activity_url',
                  'included',
                  'reason',
                  #'administrative_location_geojson',
                  #'operational_locations_geojson',
                 )



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


import pandas as pd
from django_pandas.io import read_frame
from django.utils.translation import ugettext_lazy as _
from django.core.validators import URLValidator
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from repair.apps.asmfa.models import (ActivityGroup,
                                      Activity,
                                      Actor,
                                      AdministrativeLocation,
                                      OperationalLocation,
                                      Reason,
                                      KeyflowInCasestudy,
                                      )

from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           InCasestudyField,
                                           IdentityFieldMixin,
                                           CreateWithUserInCasestudyMixin,
                                           IDRelatedField,
                                           DynamicFieldsModelSerializerMixin)


class ActivityGroupSerializer(CreateWithUserInCasestudyMixin,
                              NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'keyflow__casestudy__id',
                            'keyflow_pk': 'keyflow__id', }
    inputs = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    outputs = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    stocks = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    keyflow = IDRelatedField(read_only=True, required=False)
    nace = serializers.ListField(read_only=True, source='nace_codes')

    class Meta:
        model = ActivityGroup
        fields = ('url', 'id', 'code', 'name',
                  'inputs', 'outputs', 'stocks', 'keyflow', 'nace', 'file')


class ActivityGroupCreateSerializer(ActivityGroupSerializer):
    _upload_file = serializers.FileField(required=False, write_only=True)

    class Meta(ActivityGroupSerializer.Meta):
        extra_kwargs = {
            'code': { 'required': False },
            'name': { 'required': False }
        }
        fields = ('id', 'code', 'name', '_upload_file')

    def to_internal_value(self, data):
        """
        Convert csv-data to pandas dataframe and
        add it as attribute `dataframe` to the validated data
        add also `keyflow_id` to validated data
        """
        file = data.pop('_upload_file', None)
        ret = super().to_internal_value(data)
        if file is None:
            return ret

        encoding = 'utf8'
        df_new = pd.read_csv(file[0], sep='\t', encoding=encoding)
        df_new = df_new.\
            rename(columns={c: c.lower() for c in df_new.columns})
        ret['dataframe'] = df_new
        request = self.context['request']
        url_pks = request.session.get('url_pks', {})
        keyflow_id = url_pks.get('keyflow_pk')
        ret['keyflow_id'] = keyflow_id
        return ret

    def create(self, validated_data):
        """Bulk create of data"""
        keyflow_id = validated_data.pop('keyflow_id')
        df_ag_new = validated_data.pop('dataframe')

        index_col = 'code'
        df_ag_new.set_index(index_col, inplace=True)

        kic = KeyflowInCasestudy.objects.get(id=keyflow_id)

        # get existing activitygroups of keyflow
        qs = ActivityGroup.objects.filter(keyflow_id=kic.id)
        df_ag_old = read_frame(qs, index_col=['code'])

        existing_ag = df_ag_new.merge(df_ag_old,
                                      left_index=True,
                                      right_index=True,
                                      how='left',
                                      indicator=True,
                                      suffixes=['', '_old'])
        new_ag = existing_ag.loc[existing_ag._merge=='left_only'].reset_index()
        idx_both = existing_ag.loc[existing_ag._merge=='both'].index

        # set the KeyflowInCasestudy for the new rows
        new_ag.loc[:, 'keyflow'] = kic

        # skip columns, that are not needed
        field_names = [f.name for f in ActivityGroup._meta.fields]
        drop_cols = []
        for c in new_ag.columns:
            if not c in field_names or c.endswith('_old'):
                drop_cols.append(c)
        drop_cols.append('id')
        new_ag.drop(columns=drop_cols, inplace=True)

        # set default values for columns not provided
        defaults = {col: ActivityGroup._meta.get_field(col).default
                    for col in new_ag.columns}
        new_ag = new_ag.fillna(defaults)

        # create the new rows
        ags = []
        ag = None
        for row in new_ag.itertuples(index=False):
            row_dict = row._asdict()
            ag = ActivityGroup(**row_dict)
            ags.append(ag)
        ActivityGroup.objects.bulk_create(ags)

        # update existing values
        ignore_cols = ['id', 'keyflow']

        df_updated = df_ag_old.loc[idx_both]
        df_updated.update(df_ag_new)
        for row in df_updated.reset_index().itertuples(index=False):
            ag = ActivityGroup.objects.get(keyflow=kic,
                                           code=row.code)
            for c, v in row._asdict().items():
                if c in ignore_cols:
                    continue
                setattr(ag, c, v)
            ag.save()

        return ag


class ActivityGroupListSerializer(ActivityGroupSerializer):

    class Meta(ActivityGroupSerializer.Meta):
        fields = ('id', 'code', 'name')


class ActivityGroupField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'keyflow__casestudy__id',
                            'keyflow_pk': 'keyflow__id', }


class ActorField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'activity__activitygroup__keyflow__casestudy__id',
        'keyflow_pk': 'activity__activitygroup__keyflow__id'}


class ActorIDField(serializers.RelatedField):
    """"""
    default_error_messages = {
        'required': _('This field is required.'),
        'does_not_exist': _('Invalid Actor ID - Object does not exist.'),
        'null': _('This field may not be null.'),
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
        'keyflow_pk': 'activitygroup__keyflow__id'
    }
    activitygroup = IDRelatedField()
    activitygroup_url = ActivityGroupField(view_name='activitygroup-detail',
                                           source='activitygroup',
                                           read_only=True)
    activitygroup_name = serializers.CharField(
        source='activitygroup.name', read_only=True)

    class Meta:
        model = Activity
        fields = ('url', 'id', 'nace', 'name', 'activitygroup',
                  'activitygroup_name', 'activitygroup_url')


class ActivityListSerializer(ActivitySerializer):
    class Meta(ActivitySerializer.Meta):
        fields = ('id', 'name', 'activitygroup', 'activitygroup_name', 'nace')


class ActivityField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk':
                            'activitygroup__keyflow__casestudy__id',
                            'keyflow_pk': 'activitygroup__keyflow__id',
                            }


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
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id', }


class GeolocationInCasestudy2ListField(IdentityFieldMixin,
                                       GeolocationInCasestudySet2Field):
    """"""
    parent_lookup_kwargs = {'casestudy_pk':
                            'activity__activitygroup__keyflow__casestudy__id',
                            'actor_pk': 'id', }


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


class ActorSerializer(DynamicFieldsModelSerializerMixin,
                      CreateWithUserInCasestudyMixin,
                      NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'activity__activitygroup__keyflow__casestudy__id',
        'keyflow_pk': 'activity__activitygroup__keyflow__id',
    }
    activity = IDRelatedField()
    activity_name = serializers.CharField(source='activity.name', read_only=True)
    activitygroup_name = serializers.CharField(source='activity.activitygroup.name', read_only=True)
    activitygroup = serializers.IntegerField(source="activity.activitygroup.id",
                                             read_only=True)
    address = serializers.CharField(source='administrative_location.address', read_only=True)
    city = serializers.CharField(source='administrative_location.city', read_only=True)
    activity_url = ActivityField(view_name='activity-detail',
                                 source='activity',
                                 read_only=True)
    nace = serializers.CharField(source='activity.nace', read_only=True)

    website = URLFieldWithoutProtocol(required=False, default="",
                                      allow_blank=True)
    reason = IDRelatedField(allow_null=True)

    class Meta:
        model = Actor
        fields = ('url', 'id', 'BvDid', 'name', 'consCode', 'year', 'turnover',
                  'employees', 'BvDii', 'website', 'activity', 'activity_url',
                  'activity_name', 'activitygroup', 'activitygroup_name',
                  'included', 'nace', 'city', 'address',
                  'reason', 'description'
                  )
        extra_kwargs = {'year': {'allow_null': True},
                        'turnover': {'allow_null': True},
                        'employees': {'allow_null': True}}

    # normally you can't upload empty strings for number fields, but we want to
    # allow some of them to be blank -> set to None when receiving empty string
    def to_internal_value(self, data):
        allow_blank_numbers = ['year', 'turnover', 'employees']
        for field in allow_blank_numbers:
            if (field in data and data[field] == ''):
                data[field] = None
        return super().to_internal_value(data)


class ActorListSerializer(ActorSerializer):
    class Meta(ActorSerializer.Meta):
        fields = ('id', 'activity',  'activity_name', 'activitygroup',
                  'activitygroup_name', 'name', 'included', 'city', 'address')


class ReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reason
        fields = ('id', 'reason')

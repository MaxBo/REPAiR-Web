from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from repair.apps.asmfa.models import (Actor,
                                      AdministrativeLocation,
                                      OperationalLocation,
                                      )

from repair.apps.login.serializers import NestedHyperlinkedModelSerializer
from repair.apps.studyarea.models import Area, AdminLevels

from .nodes import ActorIDField


class PatchFields:

    @property
    def fields(self):
        fields = super().fields
        for fn in ['type', 'geometry', 'properties']:
            if fn not in fields:
                fields[fn] = serializers.CharField(write_only=True,
                                                   required=False)
        return fields


class AdministrativeLocationSerializer(PatchFields,
                                       GeoFeatureModelSerializer,
                                       NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk':
        'actor__activity__activitygroup__keyflow__casestudy__id',
        'keyflow_pk':
        'actor__activity__activitygroup__keyflow__id', }
    actor = ActorIDField()
    area = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                              queryset=Area.objects.all())
    level = serializers.PrimaryKeyRelatedField(
        required=False, allow_null=True,
        queryset=AdminLevels.objects.all(),
        #source='area.adminlevel', 
    )

    class Meta:
        model = AdministrativeLocation
        geo_field = 'geom'
        fields = ['id', 'url', 'address', 'postcode', 'country',
                  'city', 'geom', 'name',
                  'actor',
                  'area',
                  'level'
                  ]

    def create(self, validated_data):
        """Create a new AdministrativeLocation"""
        if self.Meta.model.objects.all().filter(actor=validated_data['actor']):
            msg = _('Actor <{}> already has an administrative location (has to be unique).'
                    .format(validated_data['actor']))
            raise ValidationError(detail=msg)
        return super().create(validated_data)


class AdministrativeLocationOfActorSerializer(AdministrativeLocationSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk':
        'actor__activity__activitygroup__keyflow__casestudy__id',
        'keyflow_pk':
        'actor__activity__activitygroup__keyflow__id',
        'actor_pk': 'actor__id', }
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
                  'area',
                  ]


class OperationalLocationSerializer(PatchFields,
                                    GeoFeatureModelSerializer,
                                    NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk':
        'actor__activity__activitygroup__keyflow__casestudy__id',
        'keyflow_pk':
        'actor__activity__activitygroup__keyflow__id', }
    actor = ActorIDField()
    area = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                              queryset=Area.objects.all())
    level = serializers.PrimaryKeyRelatedField(
        required=False, allow_null=True,
        queryset=AdminLevels.objects.all(),
        #source='area.adminlevel', 
    )

    class Meta:
        model = OperationalLocation
        geo_field = 'geom'
        fields = ['id', 'url', 'address', 'postcode', 'country',
                  'city', 'geom', 'name', 'actor',
                  'area', 'level']


class OperationalLocationsOfActorSerializer(OperationalLocationSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk':
        'actor__activity__activitygroup__keyflow__casestudy__id',
        'keyflow_pk':
        'actor__activity__activitygroup__keyflow__id',
        'actor_pk': 'actor__id', }
    
    class Meta(OperationalLocationSerializer.Meta):
        fields = ['id', 'url', 'address', 'postcode', 'country',
                  'city', 'geom', 'name', 'actor',
                  'area']

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

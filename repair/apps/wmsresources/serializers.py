import datetime
from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _
from django.core.validators import URLValidator
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError


from repair.apps.login.models import CaseStudy
from repair.apps.wmsresources.models import (WMSResourceInCasestudy,
                                             WMSResource,
                                             )
from wms_client.models import WMSLayer, LayerStyle

from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer,
                                           InCasestudySerializerMixin,)


class LayerStyleSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}

    class Meta:
        model = LayerStyle
        fields = (
            'id',
            'title',
            'legend_uri',
            )


class WMSLayerSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}

    styles = LayerStyleSerializer(source='layerstyle_set',
                                  many=True)

    class Meta:
        model = WMSLayer
        fields = (
            'id',
            'name',
            'title',
            'styles',
            )


class WMSResourceInCasestudySerializer(InCasestudySerializerMixin,
                                       NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}

    wmsresource_id = serializers.CharField(source='wmsresource.id',
                                           required=False)
    casestudy = serializers.IntegerField(required=False, write_only=True)
    wms_uri = serializers.CharField(source='wmsresource.uri')
    name = serializers.CharField(source='wmsresource.name')
    layers = WMSLayerSerializer(source='wmsresource.wmslayer_set', many=True)
    description = serializers.CharField(source='wmsresource.description')

    class Meta:
        model = WMSResourceInCasestudy
        fields = ('url',
                  'id',
                  'wmsresource_id',
                  'casestudy',
                  'wms_uri',
                  'name',
                  'layers',
                  'description',
                  )

    def create(self, validated_data):
        """Create a new WMSResource in casestury"""
        casestudy_id = validated_data.pop('casestudy_id', None)
        if casestudy_id:
            casestudy = CaseStudy.objects.get(pk=casestudy_id)
        else:
            casestudy = self.get_casestudy()
        wmsresource_data = validated_data.pop('wmsresource', {})
        wmsresource, created = WMSResource.objects.get_or_create(
            **wmsresource_data)
        obj = self.Meta.model.objects.create(
            casestudy=casestudy,
            wmsresource=wmsresource,
            **validated_data)
        return obj

    def update(self, instance, validated_data):
        wmsresource = WMSResource.objects.get(
            wmsresourceincasestudy=instance.pk)
        wmsresource_data = validated_data.pop('wmsresource', {})
        for attr, value in wmsresource_data.items():
            setattr(wmsresource, attr, value)
        wmsresource.save()
        return super().update(instance, validated_data)

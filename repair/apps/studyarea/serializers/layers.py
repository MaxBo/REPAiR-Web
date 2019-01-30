from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from django.db.models import Max
from django.urls import reverse

from repair.apps.studyarea.models import (LayerCategory, Layer)
from repair.apps.login.serializers import IDRelatedField


class LayerCategorySerializer(serializers.ModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    order = serializers.IntegerField(required=False, default=None)

    class Meta:
        model = LayerCategory
        fields = ('id', 'name', 'order')

    def create(self, validated_data):
        # if order is not passed, set it to current max value + 1
        if not validated_data.get('order'):
            categories = self.Meta.model.objects.filter(
                casestudy_id=validated_data.get('casestudy_id'))
            max_order = categories.aggregate(Max('order'))['order__max']
            validated_data['order'] = max_order + 1
        return super().create(validated_data)


class LayerSerializer(serializers.ModelSerializer):
    lookup_url_kwarg = 'layercategory_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'category__casestudy__id',
                            'layercategory_pk': 'category__id'}
    category = IDRelatedField(read_only=True)
    style = IDRelatedField(allow_null=True)
    order = serializers.IntegerField(required=False, default=None)
    proxy_uri = serializers.SerializerMethodField()
    legend_proxy_uri = serializers.SerializerMethodField()
    #wmsresource_uri = serializers.CharField(source="wms_layer.wmsresource.uri")

    class Meta:
        model = Layer
        fields = ('id', 'name', 'included', 'wms_layer', 'category', 'order',
                  'style', 'legend_uri', 'proxy_uri', 'legend_proxy_uri')
        #, 'wmsresource_uri')

    def get_proxy_uri(self, obj):
        return reverse('wms_proxy', args=(obj.id, ))

    def get_legend_proxy_uri(self, obj):
        uri = obj.legend_uri
        if not uri:
            return ''
        split = obj.legend_uri.split('?')
        params = split[1] if len(split) > 1 else ''
        return self.get_proxy_uri(obj) + '?' + params

    def create(self, validated_data):
        # if order is not passed, set it to current max value + 1
        if not validated_data.get('order'):
            layers = self.Meta.model.objects.filter(
                category_id=validated_data.get('category_id'))
            max_order = layers.aggregate(Max('order'))['order__max'] or 0
            validated_data['order'] = max_order + 1
        return super().create(validated_data)

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from repair.apps.studyarea.models import (LayerCategory, Layer)
from repair.apps.login.serializers import IDRelatedField


class LayerCategorySerializer(serializers.ModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}

    class Meta:
        model = LayerCategory
        fields = ('id', 'name')


class LayerSerializer(serializers.ModelSerializer):
    lookup_url_kwarg = 'layercategory_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'category__casestudy__id',
                            'layercategory_pk': 'category__id'}
    category = IDRelatedField(read_only=True)

    class Meta:
        model = Layer
        fields = ('id', 'name', 'included', 'wms_layer', 'category', 'z_index')


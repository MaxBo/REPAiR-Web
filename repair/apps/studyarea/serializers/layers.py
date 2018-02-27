from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from repair.apps.studyarea.models import (LayerCategory, Layer)


class LayerCategorySerializer(serializers.ModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}

    class Meta:
        model = LayerCategory
        fields = ('id', 'casestudy', 'name')


class LayerSerializer(serializers.ModelSerializer):
    lookup_url_kwarg = 'layercategory_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'category__casestudy__id',
                            'layercategory_pk': 'category__id'}

    class Meta:
        model = Layer
        fields = ('id', 'category', 'name', 'url', 'description', 'user', 'password')
        extra_kwargs = {
            'user': {'write_only': True},
            'password': {'write_only': True}
        }


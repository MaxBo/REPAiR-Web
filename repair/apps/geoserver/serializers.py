from rest_framework import serializers


class GeoserverLayer(object):
    def __init__(self, **kwargs):
        for field in ('id', 'name', 'namespace', 'href', 'srs', 'bbox'):
            setattr(self, field, kwargs.get(field, None))


class GeoserverLayerSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=256)
    name = serializers.CharField(max_length=256)
    namespace = serializers.CharField(max_length=256)
    href = serializers.CharField(max_length=256)
    srs = serializers.CharField(max_length=12)
    bbox = serializers.JSONField()
    

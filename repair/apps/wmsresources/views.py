# API View

from rest_framework.viewsets import ReadOnlyModelViewSet
from reversion.views import RevisionMixin
from django.views import View
from django.http import HttpResponse
import requests

from repair.apps.utils.views import ModelReadPermissionMixin
from repair.apps.wmsresources.models import WMSResourceInCasestudy
from repair.apps.studyarea.models import Layer, LayerStyle
from repair.apps.wmsresources.serializers import (
    WMSResourceInCasestudySerializer,
)

from repair.apps.utils.views import CasestudyReadOnlyViewSetMixin


class WMSResourceInCasestudyViewSet(RevisionMixin,
                                    CasestudyReadOnlyViewSetMixin,
                                    ModelReadPermissionMixin,
                                    ReadOnlyModelViewSet):
    queryset = WMSResourceInCasestudy.objects.all()
    serializer_class = WMSResourceInCasestudySerializer


class WMSProxyView(View):
    def get(self, request, layer_id):
        try:
            layer = Layer.objects.get(id=layer_id)
        except Layer.DoesNotExist:
            return HttpResponse(status=404)
        wms_layer = layer.wms_layer
        res = wms_layer.wmsresource
        uri = res.uri
        auth = (res.username, res.password) if (res.username) else None
        query_params = request.GET.copy()
        query_params['LAYERS'] = wms_layer.name
        if layer.style:
            query_params['STYLES'] = layer.style.name
        response = requests.get(uri, params=query_params, auth=auth)
        content_type = response.headers['content-type']
        return HttpResponse(response.content, content_type=content_type,
                            status=response.status_code)

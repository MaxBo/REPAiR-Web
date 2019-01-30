# API View

from rest_framework.viewsets import ReadOnlyModelViewSet
from reversion.views import RevisionMixin
from django.views import View
from django.http import HttpResponse
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from repair.apps.utils.views import ModelReadPermissionMixin
from repair.apps.wmsresources.models import WMSResourceInCasestudy
from repair.apps.studyarea.models import Layer, LayerStyle
from repair.apps.wmsresources.serializers import (
    WMSResourceInCasestudySerializer,
)

from repair.apps.utils.views import CasestudyReadOnlyViewSetMixin


def retry_session(retries=3, backoff_factor=0.3,
                  status_forcelist=(500, 502, 504),
                  session=None):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


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
        query_params = request.GET.copy()
        query_params['LAYERS'] = wms_layer.name
        query_params['query_layers'] = wms_layer.name
        if layer.style:
            query_params['STYLES'] = layer.style.name
        session = requests.Session()
        if res.username:
            session.auth = (res.username, res.password)
        session.params = query_params
        try:
            response = retry_session(session=session).get(
                uri, auth=(res.username, res.password),
                timeout=0.5)
        except Exception as e:
            print(e)
            return HttpResponse(status=502)
        else:
            content_type = response.headers['content-type']
        return HttpResponse(response.content, content_type=content_type,
                            status=response.status_code)


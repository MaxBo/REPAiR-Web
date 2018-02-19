from rest_framework import exceptions, viewsets
from rest_framework.response import Response
from django.http import HttpResponse
from django.views import View
import requests

from repair.apps.geoserver.serializers import (GeoserverLayerSerializer,
                                               GeoserverLayer)
from repair.settings import GEOSERVER_URL, GEOSERVER_PASS, GEOSERVER_USER


class GeoserverLayerViewSet(viewsets.ViewSet):
    # Required for the Browsable API renderer to have a nice form.
    serializer_class = GeoserverLayerSerializer
    rest_url = GEOSERVER_URL + '/rest/layers'

    def list(self, request):
        
        # query the geoserver "rest" api for layers, should return a json
        # with links to the resources (not very restful)
        auth = (GEOSERVER_USER, GEOSERVER_PASS)
        response = requests.get(self.rest_url, auth=auth)
        try:
            json = response.json()
        except:
            return Response(status=response.status_code)
        layers = []
        
        # iterate the responded links and try to get the real resources 
        # behind those
        for l in json['layers']['layer']:
            url = l['href']
            url = url.replace('http:', 'https:')
            res = requests.get(url, auth=auth)
            try:
                # geoserver api heavily chains the responses for some reason,
                # follow the chain
                url_2 = res.json()['layer']['resource']['href']
                url_2 = url_2.replace('http:', 'https:')
                res_2 = requests.get(url_2, auth=auth)
                l_2 = res_2.json()['featureType']
                # finally we got the resource
                namespace = l_2['namespace']['name']
                name = l_2['name']
                layer = GeoserverLayer(
                    id='{}:{}'.format(namespace, name),
                    namespace=namespace,
                    href=url_2,
                    name=name,
                    srs=l_2['srs'],
                    bbox=l_2['nativeBoundingBox'],
                )
                layers.append(layer)
            # happens when there are url related characters in the name of
            # the layer, like '.' - don't name them like that!!!!!!
            except ValueError:
                print('Warning: dead link "{}"'.format(url))
            
        serializer = self.serializer_class(instance=layers, many=True)
            
        return Response(serializer.data)


class GeoserverIndexView(View):

    def get(self, request, *args, **kwargs):
        return HttpResponse('<a href="{url}" target="_blank">{url}</a>'
                            .format(url=GEOSERVER_URL))


class GeoserverOwsView(View):
    url = 'https://geoserver.h2020repair.bk.tudelft.nl/geoserver/napoli/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=napoli:clc12&maxFeatures=50&srsname=EPSG:3857&outputFormat=application%2Fjson'
    def get(self, request, *args, **kwargs):
        auth = (GEOSERVER_USER, GEOSERVER_PASS)
        response = requests.get(self.url, auth=auth)
        content_type = response.headers['content-type']
        return HttpResponse(response.content, content_type=content_type,
                            status=response.status_code)
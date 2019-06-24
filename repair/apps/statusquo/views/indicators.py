from reversion.views import RevisionMixin
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnList
from rest_framework.decorators import action
from django.http import Http404, HttpResponseBadRequest
from django.utils.translation import ugettext as _

from repair.apps.utils.views import (ModelPermissionViewSet,
                                     CasestudyViewSetMixin)
from repair.apps.changes.models import Strategy
from repair.apps.statusquo.models import FlowIndicator
from repair.apps.statusquo.serializers import FlowIndicatorSerializer
from repair.apps.studyarea.models import Area



class FlowIndicatorViewSet(RevisionMixin, CasestudyViewSetMixin,
                           ModelPermissionViewSet):
    '''
    view on indicators in db
    '''
    queryset = FlowIndicator.objects.order_by('id')
    serializer_class = FlowIndicatorSerializer

    def destroy(self, request, **kwargs):
        instance = FlowIndicator.objects.get(id=kwargs['pk'])
        for flow in [instance.flow_a, instance.flow_b]:
            if flow:
                flow.delete()
        return super().destroy(request, **kwargs)

    @action(methods=['get', 'post'], detail=True)
    def compute(self, request, **kwargs):
        self.check_permission(request, 'view')
        indicator = self.get_queryset().get(id=kwargs.get('pk', None))
        query_params = request.query_params
        body_params = request.data
        if not indicator:
            raise Http404
        compute_class = indicator.get_type()
        geom = body_params.get('geom', None) or query_params.get('geom', None)
        if geom == 'null':
            geom = None
        areas = (body_params.get('areas', None) or
                 query_params.get('areas', None))
        aggregate = (body_params.get('aggregate', None) or
                     query_params.get('aggregate', None))
        strategy = (body_params.get('strategy', None) or
                    query_params.get('strategy', None))
        if strategy:
            strategy = Strategy.objects.get(id=strategy)
            if strategy.status == 0:
                return HttpResponseBadRequest(
                    _('calculation is not done yet'))
            if strategy.status == 1:
                return HttpResponseBadRequest(
                    _('calculation is still in process'))
        compute = compute_class(strategy=strategy)
        if aggregate is not None:
            aggregate = aggregate.lower() == 'true'
        if areas:
            areas = areas.split(',')
            areas = Area.objects.filter(id__in=areas)
        values = compute.calculate(indicator, areas=areas or [], geom=geom,
                                  aggregate=aggregate)
        return Response(values)

    def get_queryset(self):
        keyflow_pk = self.kwargs.get('keyflow_pk')
        queryset = self.queryset
        if keyflow_pk is not None:
            queryset = queryset.filter(keyflow__id=keyflow_pk)
        return queryset

from reversion.views import RevisionMixin
from repair.apps.utils.views import ModelPermissionViewSet
from repair.apps.statusquo.models import FlowIndicator
from repair.apps.statusquo.serializers import FlowIndicatorSerializer


class FlowIndicatorViewSet(RevisionMixin, ModelPermissionViewSet):
    queryset = FlowIndicator.objects.order_by('id')
    serializer_class = FlowIndicatorSerializer
    
    def destroy(self, request, **kwargs):
        instance = FlowIndicator.objects.get(id=kwargs['pk'])
        for flow in [instance.flow_a, instance.flow_b]:
            if flow:
                flow.delete()
        return super().destroy(request, **kwargs)
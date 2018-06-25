from reversion.views import RevisionMixin
from repair.apps.utils.views import ModelPermissionViewSet
from repair.apps.statusquo.models import FlowIndicator
from repair.apps.statusquo.serializers import FlowIndicatorSerializer


class FlowIndicatorViewSet(RevisionMixin, ModelPermissionViewSet):
    queryset = FlowIndicator.objects.order_by('id')
    serializer_class = FlowIndicatorSerializer
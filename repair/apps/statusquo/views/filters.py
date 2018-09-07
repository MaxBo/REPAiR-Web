from reversion.views import RevisionMixin

from repair.apps.utils.views import ModelPermissionViewSet
from repair.apps.statusquo.models import FlowFilter
from repair.apps.statusquo.serializers import FlowFilterSerializer


class FlowFilterViewSet(RevisionMixin, ModelPermissionViewSet):
    '''
    view on flow filters in db
    '''
    queryset = FlowFilter.objects.order_by('id')
    serializer_class = FlowFilterSerializer

    def get_queryset(self):
        keyflow_pk = self.kwargs.get('keyflow_pk')
        queryset = self.queryset
        if keyflow_pk is not None:
            queryset = queryset.filter(keyflow__id=keyflow_pk)
        return queryset


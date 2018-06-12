
from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet)

from repair.apps.studyarea.models import ChartCategory, Chart

from repair.apps.studyarea.serializers import (ChartCategorySerializer,
                                               ChartSerializer)


class ChartCategoryViewSet(CasestudyViewSetMixin,
                                 ModelPermissionViewSet):
    queryset = ChartCategory.objects.all()
    serializer_class = ChartCategorySerializer


class ChartViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    queryset = Chart.objects.all()
    serializer_class = ChartSerializer

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import exceptions

from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet)

from repair.apps.studyarea.models import (LayerCategory, Layer)

from repair.apps.studyarea.serializers import (LayerCategorySerializer,
                                               LayerSerializer)


class LayerCategoryViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    queryset = LayerCategory.objects.all()
    serializer_class = LayerCategorySerializer


class LayerViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer
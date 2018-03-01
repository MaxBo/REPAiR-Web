# API View
from abc import ABC

from rest_framework.viewsets import ReadOnlyModelViewSet
from reversion.views import RevisionMixin
from repair.apps.utils.views import ModelReadPermissionMixin
from repair.apps.wmsresources.models import (
    WMSResourceInCasestudy,
)

from repair.apps.wmsresources.serializers import (
    WMSResourceInCasestudySerializer,
)

from repair.apps.login.views import CasestudyReadOnlyViewSetMixin


class WMSResourceInCasestudyViewSet(RevisionMixin,
                                    CasestudyReadOnlyViewSetMixin,
                                    ModelReadPermissionMixin,
                                    ReadOnlyModelViewSet):
    queryset = WMSResourceInCasestudy.objects.all()
    serializer_class = WMSResourceInCasestudySerializer
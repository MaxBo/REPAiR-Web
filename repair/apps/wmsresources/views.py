# API View
from abc import ABC

from rest_framework.viewsets import ModelViewSet
from reversion.views import RevisionMixin
from repair.apps.utils.views import ModelPermissionViewSet
from repair.apps.wmsresources.models import (
    WMSResourceInCasestudy,
)

from repair.apps.wmsresources.serializers import (
    WMSResourceInCasestudySerializer,
)

from repair.apps.login.views import CasestudyViewSetMixin


class WMSResourceInCasestudyViewSet(RevisionMixin,
                                    CasestudyViewSetMixin,
                                    ModelPermissionViewSet):
    queryset = WMSResourceInCasestudy.objects.all()
    serializer_class = WMSResourceInCasestudySerializer
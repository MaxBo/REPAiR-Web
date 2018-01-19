# API View
from abc import ABC

from rest_framework.viewsets import ModelViewSet
from reversion.views import RevisionMixin

from repair.apps.publications.models import (
    PublicationInCasestudy,
)

from repair.apps.publications.serializers import (
    PublicationInCasestudySerializer,
)

from repair.apps.login.views import CasestudyViewSetMixin, OnlySubsetMixin


class PublicationInCasestudyViewSet(RevisionMixin,
                                    CasestudyViewSetMixin,
                                    ModelViewSet):
    queryset = PublicationInCasestudy.objects.all()
    serializer_class = PublicationInCasestudySerializer
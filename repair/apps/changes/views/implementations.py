
from repair.apps.login.views import CasestudyViewSetMixin

from repair.apps.utils.views import ReadUpdateViewSet
from repair.apps.changes.models import (
    Implementation,
    SolutionInImplementation,
    SolutionInImplementationNote,
    SolutionInImplementationQuantity,
    SolutionInImplementationGeometry,

    )

from repair.apps.changes.serializers import (
    ImplementationSerializer,
    SolutionInImplementationSerializer,
    SolutionInImplementationNoteSerializer,
    SolutionInImplementationQuantitySerializer,
    SolutionInImplementationGeometrySerializer,
    ImplementationOfUserSerializer,
    )

from repair.apps.utils.views import ModelPermissionViewSet


class ImplementationViewSet(CasestudyViewSetMixin,
                            ModelPermissionViewSet):
    serializer_class = ImplementationSerializer
    queryset = Implementation.objects.all()


class ImplementationOfUserViewSet(ImplementationViewSet):
    # TODO: find th permissions
    serializer_class = ImplementationOfUserSerializer


class SolutionInImplementationViewSet(CasestudyViewSetMixin,
                                      ModelPermissionViewSet):
    serializer_class = SolutionInImplementationSerializer
    queryset = SolutionInImplementation.objects.all()


class SolutionInImplementationNoteViewSet(CasestudyViewSetMixin,
                                      ModelPermissionViewSet):
    serializer_class = SolutionInImplementationNoteSerializer
    queryset = SolutionInImplementationNote.objects.all()


class SolutionInImplementationQuantityViewSet(CasestudyViewSetMixin,
                                              ReadUpdateViewSet):
    """
    Has to provide exactly one quantity value
    for each quantity defined for the solution
    So no PUT or DELETE is allowed
    """
    serializer_class = SolutionInImplementationQuantitySerializer
    queryset = SolutionInImplementationQuantity.objects.all()


class SolutionInImplementationGeometryViewSet(CasestudyViewSetMixin,
                                              ModelPermissionViewSet):
    serializer_class = SolutionInImplementationGeometrySerializer
    queryset = SolutionInImplementationGeometry.objects.all()

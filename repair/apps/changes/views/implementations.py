
from repair.apps.login.views import CasestudyViewSetMixin

from repair.apps.utils.views import ReadUpdateViewSet
from repair.apps.changes.models import (
    Implementation,
    SolutionInImplementation,
    SolutionInImplementationQuantity,

    )

from repair.apps.changes.serializers import (
    ImplementationSerializer,
    SolutionInImplementationSerializer,
    SolutionInImplementationQuantitySerializer,
    )

from repair.apps.utils.views import (ModelPermissionViewSet,
                                     ReadUpdatePermissionViewSet)


class ImplementationViewSet(CasestudyViewSetMixin,
                            ModelPermissionViewSet):
    serializer_class = ImplementationSerializer
    queryset = Implementation.objects.all()
    
    def list(self, request, *args, **kwargs):
        
        if (request.user.id and 'user' not in request.query_params and
            'user__in' not in request.query_params):
            self.queryset = self.queryset.filter(user__user__user_id=request.user.id)
        
        return super().list(request, *args, **kwargs)


class SolutionInImplementationViewSet(CasestudyViewSetMixin,
                                      ModelPermissionViewSet):
    serializer_class = SolutionInImplementationSerializer
    queryset = SolutionInImplementation.objects.all()


class SolutionInImplementationQuantityViewSet(CasestudyViewSetMixin,
                                              ReadUpdatePermissionViewSet):
    """
    Has to provide exactly one quantity value
    for each quantity defined for the solution
    So no PUT or DELETE is allowed
    """
    serializer_class = SolutionInImplementationQuantitySerializer
    queryset = SolutionInImplementationQuantity.objects.all()

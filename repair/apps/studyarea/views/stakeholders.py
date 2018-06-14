
from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet)

from repair.apps.studyarea.models import (StakeholderCategory,
                                          Stakeholder,
                                          )

from repair.apps.studyarea.serializers import (StakeholderCategorySerializer,
                                               StakeholderSerializer,
                                               )


class StakeholderCategoryViewSet(CasestudyViewSetMixin,
                                 ModelPermissionViewSet):
    queryset = StakeholderCategory.objects.all()
    serializer_class = StakeholderCategorySerializer


class StakeholderViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    queryset = Stakeholder.objects.all()
    serializer_class = StakeholderSerializer

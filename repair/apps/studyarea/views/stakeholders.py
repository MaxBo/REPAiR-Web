
from repair.apps.login.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet)

from repair.apps.studyarea.models import (StakeholderCategory,
                                          Stakeholder,
                                          )

from repair.apps.studyarea.serializers import (StakeholderCategorySerializer,
                                               StakeholderSerializer,
                                               )


class StakeholderCategoryViewSet(CasestudyViewSetMixin,
                                 ModelPermissionViewSet):
    add_perm = 'studyarea.add_stakeholdercategory'
    change_perm = 'studyarea.change_stakeholdercategory'
    delete_perm = 'studyarea.delete_stakeholdercategory'
    queryset = StakeholderCategory.objects.all()
    serializer_class = StakeholderCategorySerializer


class StakeholderViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    add_perm = 'studyarea.add_stakeholder'
    change_perm = 'studyarea.change_stakeholder'
    delete_perm = 'studyarea.delete_stakeholder'
    queryset = Stakeholder.objects.all()
    serializer_class = StakeholderSerializer

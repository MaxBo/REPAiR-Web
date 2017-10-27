from rest_framework_nested.routers import NestedSimpleRouter, DefaultRouter
from django.conf.urls import url, include

from repair.apps.login import views as login_views
from repair.apps.studyarea.views import (
    StakeholderCategoryViewSet, StakeholderViewSet)
from repair.apps.changes.views import (
    SolutionCategoryViewSet, SolutionViewSet)
from repair.apps.asmfa.views import (
    ActivityGroupViewSet, ActivityViewSet, ActorViewSet,
    Activity2ActivityViewSet, MaterialViewSet, Group2GroupViewSet,
    Actor2ActorViewSet, QualityViewSet)

## base routes ##

router = DefaultRouter()
router.register(r'users', login_views.UserViewSet)
router.register(r'groups', login_views.GroupViewSet)
router.register(r'casestudies', login_views.CaseStudyViewSet)
router.register(r'stakeholder_categories', StakeholderCategoryViewSet)
router.register(r'stakeholders', StakeholderViewSet)
router.register(r'solution_categories', SolutionCategoryViewSet, base_name='solutioncategories')
router.register(r'solutions', SolutionViewSet, base_name='solutions')

## nested routes (see https://github.com/alanjds/drf-nested-routers) ##

# /casestudies/...
cs_router = NestedSimpleRouter(router, r'casestudies', lookup='casestudy')
cs_router.register(r'activitygroups', ActivityGroupViewSet, base_name='activitygroups')
cs_router.register(r'activities', ActivityViewSet, base_name='activities')
cs_router.register(r'actors', ActorViewSet, base_name='actors')
cs_router.register(r'solutioncategories', SolutionCategoryViewSet, base_name='solutioncategories')
cs_router.register(r'materials', MaterialViewSet, base_name='materials')
cs_router.register(r'qualities', QualityViewSet, base_name='qualities')

# /casestudies/*/solutioncategories/...
scat_router = NestedSimpleRouter(cs_router, r'solutioncategories', lookup='solutioncategory')
scat_router.register(r'solutions', SolutionViewSet, base_name='solutions')

# /casestudies/*/activitygroups/...
ag_router = NestedSimpleRouter(cs_router, r'activitygroups', lookup='activitygroup')
ag_router.register(r'activities', ActivityViewSet, base_name='activities')

# /casestudies/*/activitygroups/*/activities/...
ac_router = NestedSimpleRouter(ag_router, r'activities', lookup='activity')
ac_router.register(r'actors', ActorViewSet, base_name='actors')

# /casestudies/*/materials/...
mat_router = NestedSimpleRouter(cs_router, r'materials', lookup='material')
mat_router.register(r'group2group', Group2GroupViewSet,
                    base_name='group2group')
mat_router.register(r'activity2activity', Activity2ActivityViewSet,
                    base_name='activity2activity')
mat_router.register(r'actor2actor', Actor2ActorViewSet,
                    base_name='actor2actor')


## webhook ##

url(r'^api/payload', include('repair.static.webhook.urls'))

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^', include(cs_router.urls)),
    url(r'^', include(ag_router.urls)),
    url(r'^', include(scat_router.urls)),
    url(r'^', include(ac_router.urls)),
    url(r'^', include(mat_router.urls))
]

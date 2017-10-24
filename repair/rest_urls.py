from rest_framework_nested.routers import NestedSimpleRouter, DefaultRouter
from django.conf.urls import url, include

from repair.apps.login import views as login_views
from repair.apps.changes.views import (
    CaseStudyViewSet, StakeholderCategoryViewSet, StakeholderViewSet, 
    SolutionCategoryViewSet, SolutionViewSet,
    )
from repair.apps.asmfa.views import ActivityGroupViewSet

## base routes ##

router = DefaultRouter()
router.register(r'users', login_views.UserViewSet)
router.register(r'groups', login_views.GroupViewSet)
router.register(r'casestudies', CaseStudyViewSet)
router.register(r'stakeholder_categories', StakeholderCategoryViewSet)
router.register(r'stakeholders', StakeholderViewSet)
router.register(r'solution_categories', SolutionCategoryViewSet, base_name='solutioncategories')
router.register(r'solutions', SolutionViewSet, base_name='solutions')

## nested routes (see https://github.com/alanjds/drf-nested-routers) ##

# /casestudies
cs_router = NestedSimpleRouter(router, r'casestudies', lookup='casestudy')
cs_router.register(r'activitygroups', ActivityGroupViewSet, base_name='activitygroups')
cs_router.register(r'solutioncategories', SolutionCategoryViewSet, base_name='solutioncategories')

# /casestudies/*/activitygroups
ag_router = NestedSimpleRouter(cs_router, r'activitygroups', lookup='activitygroup')

# /casestudies/*/solutioncategories
scat_router = NestedSimpleRouter(cs_router, r'solutioncategories', lookup='solutioncategory')
scat_router.register(r'solutions', SolutionViewSet, base_name='solutions')

## webhook ##

url(r'^api/payload', include('repair.static.webhook.urls'))

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^', include(cs_router.urls)),
    url(r'^', include(ag_router.urls)),
    url(r'^', include(scat_router.urls))
]

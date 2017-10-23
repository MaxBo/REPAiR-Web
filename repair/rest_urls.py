from rest_framework_nested.routers import NestedSimpleRouter, DefaultRouter
from django.conf.urls import url, include

from repair.apps.login import views as login_views
from repair.apps.changes.views import (
    SolutionCategoriesListApiView,
    SolutionCategoryApiView,
    SolutionsListApiView,
    SolutionApiView,
    )
from repair.apps.asmfa.views import ActivityGroupsListApiView
from repair.apps.changes.views import (CaseStudyViewSet,
                                       StakeholderCategoryViewSet,
                                       StakeholderViewSet,
                                       SolutionCategoryViewSet,
                                       SolutionViewSet,
                                       )

router = DefaultRouter()
router.register(r'users', login_views.UserViewSet)
router.register(r'groups', login_views.GroupViewSet)
router.register(r'casestudies', CaseStudyViewSet)
router.register(r'stakeholder_categories', StakeholderCategoryViewSet)
router.register(r'stakeholders', StakeholderViewSet)
router.register(r'solution_categories', SolutionCategoryViewSet)
router.register(r'solutions', SolutionViewSet)

cs_router = NestedSimpleRouter(router, 'casestudies', lookup='casestudy')
cs_router.register(r'activitygroups', ActivityGroupsListApiView, base_name='activitygroups')

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^', include(cs_router.urls))
]

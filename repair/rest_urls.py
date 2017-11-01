from rest_framework_nested.routers import (NestedSimpleRouter, DefaultRouter,
                                           NestedDefaultRouter)
from rest_framework.documentation import include_docs_urls

from django.conf.urls import url, include

from repair.apps.login import views as login_views
from repair.apps.studyarea.views import (
    StakeholderCategoryViewSet, StakeholderViewSet)
from repair.apps.changes.views import (
    UnitViewSet,
    SolutionCategoryViewSet,
    SolutionViewSet,
    ImplementationViewSet,
    SolutionInImplementationViewSet,
    SolutionQuantityViewSet,
    SolutionRatioOneUnitViewSet,
    SolutionInImplementationNoteViewSet,
    SolutionInImplementationQuantityViewSet,
    SolutionInImplementationGeometryViewSet,
)

from repair.apps.asmfa.views import (
    ActivityGroupViewSet, ActivityViewSet, ActorViewSet,
    Activity2ActivityViewSet, MaterialViewSet, Group2GroupViewSet,
    Actor2ActorViewSet, QualityViewSet)

## base routes ##

router = DefaultRouter()
router.register(r'users', login_views.UserViewSet)
router.register(r'groups', login_views.GroupViewSet)
router.register(r'casestudies', login_views.CaseStudyViewSet)
router.register(r'units', UnitViewSet)

## nested routes (see https://github.com/alanjds/drf-nested-routers) ##

# /casestudies/...
cs_router = NestedDefaultRouter(router, r'casestudies', lookup='casestudy')
cs_router.register(r'users', login_views.UserInCasestudyViewSet)
cs_router.register(r'activitygroups', ActivityGroupViewSet,
                   base_name='activitygroups')
cs_router.register(r'activities', ActivityViewSet, base_name='activities')
cs_router.register(r'actors', ActorViewSet, base_name='actors')
cs_router.register(r'solutioncategories', SolutionCategoryViewSet)
cs_router.register(r'stakeholdercategories', StakeholderCategoryViewSet)
cs_router.register(r'implementations', ImplementationViewSet)
cs_router.register(r'materials', MaterialViewSet, base_name='materials')
cs_router.register(r'qualities', QualityViewSet, base_name='qualities')

# /casestudies/*/stakeholdercategories/...
shcat_router = NestedSimpleRouter(cs_router, r'stakeholdercategories',
                                  lookup='stakeholdercategory')
shcat_router.register(r'stakeholders', StakeholderViewSet)

# /casestudies/*/solutioncategories/...
scat_router = NestedSimpleRouter(cs_router, r'solutioncategories',
                                 lookup='solutioncategory')
scat_router.register(r'solutions', SolutionViewSet)

# /casestudies/*/solutioncategories/*/solutions...
sol_router = NestedSimpleRouter(scat_router, r'solutions',
                                 lookup='solution')
sol_router.register(r'solutionquantities', SolutionQuantityViewSet)
sol_router.register(r'solutionratiooneunits', SolutionRatioOneUnitViewSet)

# /casestudies/*/implementations/...
imp_router = NestedSimpleRouter(cs_router, r'implementations',
                                 lookup='implementation')
imp_router.register(r'solutions', SolutionInImplementationViewSet)

# /casestudies/*/implementations/*/solutions...
sii_router = NestedSimpleRouter(imp_router, r'solutions',
                                lookup='solution')
sii_router.register(r'note', SolutionInImplementationNoteViewSet)
sii_router.register(r'quantity', SolutionInImplementationQuantityViewSet)
sii_router.register(r'geometry', SolutionInImplementationGeometryViewSet)


# /casestudies/*/activitygroups/...
ag_router = NestedSimpleRouter(cs_router, r'activitygroups',
                               lookup='activitygroup')
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
    url(r'^docs/', include_docs_urls(title='REPAiR API Documentation')),
    url(r'^', include(router.urls)),
    url(r'^', include(cs_router.urls)),
    url(r'^', include(ag_router.urls)),
    url(r'^', include(shcat_router.urls)),
    url(r'^', include(scat_router.urls)),
    url(r'^', include(sol_router.urls)),
    url(r'^', include(imp_router.urls)),
    url(r'^', include(sii_router.urls)),
    url(r'^', include(ac_router.urls)),
    url(r'^', include(mat_router.urls))
]

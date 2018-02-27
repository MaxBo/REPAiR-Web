from rest_framework_nested.routers import (NestedSimpleRouter, DefaultRouter,
                                           NestedDefaultRouter)
from rest_framework.documentation import include_docs_urls

from django.conf.urls import url, include

from repair.apps.login import views as login_views
from repair.apps.studyarea.views import (
    StakeholderCategoryViewSet,
    StakeholderViewSet,
    AdminLevelViewSet,
    AreaViewSet,
    LayerCategoryViewSet,
    LayerViewSet
)

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
    ImplementationOfUserViewSet,
    StrategyViewset,
)

from repair.apps.asmfa.views import (
    ActivityGroupViewSet,
    ActivityViewSet,
    ActorViewSet,
    ReasonViewSet, 
    Activity2ActivityViewSet,
    Group2GroupViewSet,
    Actor2ActorViewSet,
    KeyflowViewSet,
    KeyflowInCasestudyViewSet,
    GroupStockViewSet,
    ActivityStockViewSet,
    ActorStockViewSet,
    AllActivityViewSet,
    AllActorViewSet,
    AdministrativeLocationOfActorViewSet,
    OperationalLocationsOfActorViewSet,
    AdministrativeLocationViewSet,
    OperationalLocationViewSet,
    ProductViewSet,
    MaterialViewSet,
    WasteViewSet,
)

from repair.apps.utils.views import PublicationView
from repair.apps.publications.views import (PublicationInCasestudyViewSet,)


## base routes ##

router = DefaultRouter()
router.register(r'casestudies', login_views.CaseStudyViewSet)
router.register(r'units', UnitViewSet)
router.register(r'keyflows', KeyflowViewSet)
router.register(r'products', ProductViewSet)
router.register(r'wastes', WasteViewSet)
router.register(r'publications', PublicationView)
router.register(r'reasons', ReasonViewSet)

## nested routes (see https://github.com/alanjds/drf-nested-routers) ##

# /casestudies/...
cs_router = NestedDefaultRouter(router, r'casestudies', lookup='casestudy')
cs_router.register(r'users', login_views.UserInCasestudyViewSet)
cs_router.register(r'solutioncategories', SolutionCategoryViewSet)
cs_router.register(r'stakeholdercategories', StakeholderCategoryViewSet)
cs_router.register(r'implementations', ImplementationViewSet)
cs_router.register(r'strategies', StrategyViewset)
cs_router.register(r'keyflows', KeyflowInCasestudyViewSet)
cs_router.register(r'layercategories', LayerCategoryViewSet)
cs_router.register(r'levels', AdminLevelViewSet)
cs_router.register(r'publications', PublicationInCasestudyViewSet)

# /casestudies/*/layercategories/...
layercat_router = NestedSimpleRouter(cs_router, r'layercategories',
                                     lookup='layercategory')
layercat_router.register(r'layers', LayerViewSet)

# /casestudies/*/levels/...
levels_router = NestedSimpleRouter(cs_router, r'levels',
                                 lookup='level')
levels_router.register(r'areas', AreaViewSet)


# /casestudies/*/stakeholdercategories/...
user_router = NestedSimpleRouter(cs_router, r'users',
                                  lookup='user')
user_router.register(r'implementations', ImplementationOfUserViewSet)


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

# /casestudies/*/keyflows/...
kf_router = NestedSimpleRouter(cs_router, r'keyflows', lookup='keyflow')
kf_router.register(r'groupstock', GroupStockViewSet)
kf_router.register(r'activitystock', ActivityStockViewSet)
kf_router.register(r'actorstock', ActorStockViewSet)
kf_router.register(r'group2group', Group2GroupViewSet)
kf_router.register(r'activity2activity', Activity2ActivityViewSet)
kf_router.register(r'actor2actor', Actor2ActorViewSet)
kf_router.register(r'materials', MaterialViewSet)
kf_router.register(r'activitygroups', ActivityGroupViewSet)
kf_router.register(r'activities', AllActivityViewSet)
kf_router.register(r'actors', AllActorViewSet)
kf_router.register(r'administrativelocations', AdministrativeLocationViewSet)
kf_router.register(r'operationallocations', OperationalLocationViewSet)

# /casestudies/*/keyflows/*/activitygroups/...
ag_router = NestedSimpleRouter(kf_router, r'activitygroups',
                               lookup='activitygroup')
ag_router.register(r'activities', ActivityViewSet)

# /casestudies/*/keyflows/*/activitygroups/*/activities/...
ac_router = NestedSimpleRouter(ag_router, r'activities', lookup='activity')
ac_router.register(r'actors', ActorViewSet)

# /casestudies/*/keyflows/*/actors/...
actors_router = NestedSimpleRouter(kf_router, r'actors',
                                   lookup='actor')
actors_router.register(r'administrativelocation',
                   AdministrativeLocationOfActorViewSet)
actors_router.register(r'operationallocations',
                   OperationalLocationsOfActorViewSet)



## webhook ##

url(r'^api/payload', include('repair.static.webhook.urls'))

urlpatterns = [
    url(r'^docs/', include_docs_urls(title='REPAiR API Documentation')),
    url(r'^', include(router.urls)),
    url(r'^', include(cs_router.urls)),
    url(r'^', include(ag_router.urls)),
    url(r'^', include(ac_router.urls)),
    url(r'^', include(shcat_router.urls)),
    url(r'^', include(scat_router.urls)),
    url(r'^', include(sol_router.urls)),
    url(r'^', include(imp_router.urls)),
    url(r'^', include(sii_router.urls)),
    url(r'^', include(kf_router.urls)),
    url(r'^', include(user_router.urls)),
    url(r'^', include(actors_router.urls)),
    url(r'^', include(levels_router.urls)),
    url(r'^', include(layercat_router.urls)),
]

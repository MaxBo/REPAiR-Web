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
    LayerViewSet,
    ChartCategoryViewSet,
    ChartViewSet
)

from repair.apps.changes.views import (
    UnitViewSet,
    SolutionCategoryViewSet,
    SolutionViewSet,
    StrategyViewSet,
    SolutionInStrategyViewSet,
    SolutionQuantityViewSet,
    SolutionRatioOneUnitViewSet,
    SolutionInStrategyQuantityViewSet,
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
    AdministrativeLocationOfActorViewSet,
    OperationalLocationsOfActorViewSet,
    AdministrativeLocationViewSet,
    OperationalLocationViewSet,
    ProductViewSet,
    MaterialViewSet,
    AllMaterialViewSet,
    WasteViewSet,
)

from repair.apps.statusquo.views import (
    AimViewSet,
    UserObjectiveViewSet,
    ChallengeViewSet,
    FlowTargetViewSet,
    SustainabilityFieldViewSet,
    ImpactcategoryViewSet,
    ImpactCategoryInSustainabilityViewSet,
    AreaOfProtectionViewSet,
    TargetValueViewSet,
    TargetSpatialReferenceViewSet,
    FlowIndicatorViewSet,
    FlowFilterViewSet
)
from repair.apps.utils.views import PublicationView
from repair.apps.publications.views import (PublicationInCasestudyViewSet,)
from repair.apps.wmsresources.views import (WMSResourceInCasestudyViewSet, )


## base routes ##

router = DefaultRouter()
router.register(r'casestudies', login_views.CaseStudyViewSet)
router.register(r'units', UnitViewSet)
router.register(r'keyflows', KeyflowViewSet)
router.register(r'products', ProductViewSet)
router.register(r'wastes', WasteViewSet)
router.register(r'materials', AllMaterialViewSet)
router.register(r'publications', PublicationView)
router.register(r'reasons', ReasonViewSet)
router.register(r'sustainabilities', SustainabilityFieldViewSet)
router.register(r'impactcategories', ImpactcategoryViewSet)
router.register(r'targetvalues', TargetValueViewSet)
router.register(r'targetspecialreference', TargetSpatialReferenceViewSet)
router.register(r'areasofprotection', AreaOfProtectionViewSet)

## nested routes (see https://github.com/alanjds/drf-nested-routers) ##
# / sustainabilities/../
sus_router = NestedDefaultRouter(router, r'sustainabilities',
                                 lookup='sustainability')
sus_router.register(r'areasofprotection', AreaOfProtectionViewSet)
sus_router.register(r'impactcategories', ImpactCategoryInSustainabilityViewSet)

# /casestudies/...
cs_router = NestedDefaultRouter(router, r'casestudies', lookup='casestudy')
cs_router.register(r'users', login_views.UserInCasestudyViewSet)
cs_router.register(r'stakeholdercategories', StakeholderCategoryViewSet)
cs_router.register(r'chartcategories', ChartCategoryViewSet)
cs_router.register(r'keyflows', KeyflowInCasestudyViewSet)
cs_router.register(r'layercategories', LayerCategoryViewSet)
cs_router.register(r'levels', AdminLevelViewSet)
cs_router.register(r'publications', PublicationInCasestudyViewSet)
cs_router.register(r'aims', AimViewSet)
cs_router.register(r'userobjectives', UserObjectiveViewSet)
cs_router.register(r'challenges', ChallengeViewSet)
cs_router.register(r'wmsresources', WMSResourceInCasestudyViewSet)


# /casestudies/*/userobjectives/...
uo_router = NestedSimpleRouter(cs_router, r'userobjectives',
                               lookup='userobjective')
uo_router.register(r'flowtargets', FlowTargetViewSet)

# /casestudies/*/layercategories/...
layercat_router = NestedSimpleRouter(cs_router, r'layercategories',
                                     lookup='layercategory')
layercat_router.register(r'layers', LayerViewSet)

# /casestudies/*/levels/...
levels_router = NestedSimpleRouter(cs_router, r'levels',
                                 lookup='level')
levels_router.register(r'areas', AreaViewSet)

# /casestudies/*/chartcategories/...
chart_router = NestedSimpleRouter(cs_router, r'chartcategories',
                                  lookup='chartcategory')
chart_router.register(r'charts', ChartViewSet)

# /casestudies/*/stakeholdercategories/...
shcat_router = NestedSimpleRouter(cs_router, r'stakeholdercategories',
                                  lookup='stakeholdercategory')
shcat_router.register(r'stakeholders', StakeholderViewSet)

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
kf_router.register(r'activities', ActivityViewSet)
kf_router.register(r'actors', ActorViewSet)
kf_router.register(r'administrativelocations', AdministrativeLocationViewSet)
kf_router.register(r'operationallocations', OperationalLocationViewSet)
kf_router.register(r'flowindicators', FlowIndicatorViewSet)
kf_router.register(r'flowfilters', FlowFilterViewSet)
kf_router.register(r'solutioncategories', SolutionCategoryViewSet)
kf_router.register(r'strategies', StrategyViewSet)

# /casestudies/*/keyflows/*/solutioncategories/...
scat_router = NestedSimpleRouter(kf_router, r'solutioncategories',
                                 lookup='solutioncategory')
scat_router.register(r'solutions', SolutionViewSet)

# /casestudies/*/keyflows/*/solutioncategories/*/solutions...
sol_router = NestedSimpleRouter(scat_router, r'solutions',
                                 lookup='solution')
sol_router.register(r'solutionquantities', SolutionQuantityViewSet)
sol_router.register(r'solutionratiooneunits', SolutionRatioOneUnitViewSet)

# /casestudies/*/keyflows/*/strategies/...
strat_router = NestedSimpleRouter(kf_router, r'strategies',
                                lookup='strategy')
strat_router.register(r'solutions', SolutionInStrategyViewSet)

# /casestudies/*/keyflows/*/strategies/*/solutions...
sii_router = NestedSimpleRouter(strat_router, r'solutions',
                                lookup='solution')
sii_router.register(r'quantities', SolutionInStrategyQuantityViewSet)

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
    url(r'^', include(sus_router.urls)),
    url(r'^', include(cs_router.urls)),
    url(r'^', include(shcat_router.urls)),
    url(r'^', include(scat_router.urls)),
    url(r'^', include(chart_router.urls)),
    url(r'^', include(sol_router.urls)),
    url(r'^', include(strat_router.urls)),
    url(r'^', include(sii_router.urls)),
    url(r'^', include(kf_router.urls)),
    url(r'^', include(actors_router.urls)),
    url(r'^', include(levels_router.urls)),
    url(r'^', include(layercat_router.urls)),
    url(r'^', include(uo_router.urls))
]

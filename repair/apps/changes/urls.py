from django.conf.urls import url

from repair.apps.changes import views
from repair.apps.changes.views import (CaseStudyViewSet,
                                       StakeholderCategoryViewSet,
                                       StakeholderViewSet,
                                       SolutionCategoryViewSet,
                                       SolutionViewSet,
                                       )
from repair.urls import router

urlpatterns = [
    url(r'^$', views.index, name='index'),

    # ex: /5/
    url(r'^(?P<casestudy_id>[0-9]+)/$',
        views.casestudy,
        name='casestudy'),

    # ex: /5/users/3/
    url(r'^(?P<casestudy_id>[0-9]+)/users/(?P<user_id>[0-9]+)/$',
        views.userincasestudy,
        name='userincasestudy'),


    # ex: /stakeholdercategories/3
    url(r'^stakeholdercategories/(?P<stakeholder_category_id>[0-9]+)/$',
        views.stakeholder_categories,
        name='stakeholder_categories'),

    # ex: /stakeholders/3
    url(r'^stakeholders/(?P<stakeholder_id>[0-9]+)/$',
        views.stakeholders,
        name='stakeholders'),

    # ex: /implementations/3
    url(r'^implementations/(?P<implementation_id>[0-9]+)/$',
        views.implementations,
        name='implementations'),

    # ex: /solutioncategories/3
    url(r'^solutioncategories/(?P<solutioncategory_id>[0-9]+)/$',
        views.solutioncategories,
        name='solutioncategories'),

    # ex: /solutions/3
    url(r'^solutions/(?P<solution_id>[0-9]+)/$',
        views.solutions,
        name='solutions'),

    # ex: /implementations/3/solutions/2
    url(r'^implementations/(?P<implementation_id>[0-9]+)/solutions/(?P<solution_id>[0-9]+)/$',
        views.solution_in_implematation,
        name='solution_in_implementation'),

    # ex: /strategies/3/
    url(r'^strategies/(?P<strategy_id>[0-9]+)/$',
        views.strategies,
        name='strategies'),

    # ex: /users/3/
    url(r'^users/(?P<user_id>[0-9]+)/$',
        views.user,
        name='user'),

]


router.register(r'casestudy', CaseStudyViewSet)
router.register(r'stakeholder_categories', StakeholderCategoryViewSet)
router.register(r'stakeholders', StakeholderViewSet)
router.register(r'solution_categories', SolutionCategoryViewSet)
router.register(r'solutions', SolutionViewSet)

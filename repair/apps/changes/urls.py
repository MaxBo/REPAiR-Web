from django.conf.urls import url

from repair.apps.changes import views

urlpatterns = [
    url(r'^$', views.index, name='index'),

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

]
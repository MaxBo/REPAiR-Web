from django.conf.urls import url

from repair.apps.changes import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    # ex: /casestudy/5/
    url(r'^(?P<casestudy_id>[0-9]+)/$', views.casestudy, name='casestudy'),
    # ex: /stakeholdercategories/3
    url(r'^stakeholdercategories/(?P<stakeholder_category_id>[0-9]+)/$', views.stakeholder_categories, name='stakeholder_categories'),
    # ex: /stakeholders/3
    url(r'^stakeholders/(?P<stakeholder_id>[0-9]+)/$', views.stakeholders, name='stakeholders'),
    # ex: /implementations/3
    url(r'^implementations/(?P<implementation_id>[0-9]+)/$', views.implementations, name='implementations'),
    # ex: /solutions/3
    url(r'^solutions/(?P<solution_id>[0-9]+)/$', views.solutions, name='solutions'),
]
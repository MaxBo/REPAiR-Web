from django.conf.urls import url

from repair.apps.changes import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    # ex: /casestudy/5/
    url(r'^(?P<casestudy_id>[0-9]+)/$', views.casestudy, name='casestudy'),
    # ex: /casestudy/5/stakeholdercategories/3
    url(r'^(?P<casestudy_id>[0-9]+)/stakeholdercategories/(?P<stakeholder_category_id>[0-9]+)/$', views.stakeholder_categories, name='stakeholder_categories'),
    # ex: /casestudy/5/stakeholdercategories/3
    url(r'^(?P<stakeholder_id>[0-9]+)/$', views.stakeholders, name='stakeholders'),
]
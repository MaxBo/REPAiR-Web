from django.conf.urls import url

from repair.apps.study_area import views

urlpatterns = [
    url(r'^$', views.stakeholders, name='stakeholders')
]
from django.conf.urls import url

from repair.apps.decisions import views

urlpatterns = [
    url(r'^$', views.DecisionsIndexView.as_view(), name='index'),
]
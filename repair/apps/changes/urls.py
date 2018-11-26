from django.conf.urls import url

from repair.apps.changes import views

urlpatterns = [
    url(r'^$', views.StrategyIndexView.as_view(), name='index')
]

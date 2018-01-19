from django.conf.urls import url

from repair.apps.impacts import views

urlpatterns = [
    url(r'^$', views.ImpactsIndexView.as_view(), name='index'),
]
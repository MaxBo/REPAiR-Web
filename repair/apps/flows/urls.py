from django.conf.urls import url

from repair.apps.flows import views

urlpatterns = [
    url(r'^$', views.index, name='flows')
]
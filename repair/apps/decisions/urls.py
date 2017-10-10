from django.conf.urls import url

from repair.apps.decisions import views

urlpatterns = [
    url(r'^$', views.index, name='decisions')
]
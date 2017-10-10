from django.conf.urls import url

from repair.apps.status_quo import views

urlpatterns = [
    url(r'^$', views.index, name='status-quo')
]
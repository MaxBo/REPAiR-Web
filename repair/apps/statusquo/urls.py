from django.conf.urls import url

from repair.apps.statusquo import views

urlpatterns = [
    url(r'^$', views.index, name='status-quo')
]
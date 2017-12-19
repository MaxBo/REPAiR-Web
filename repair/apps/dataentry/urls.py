from django.conf.urls import url

from repair.apps.dataentry import views

urlpatterns = [
    url(r'^$', views.DataEntryView.as_view(), name='admin')
]
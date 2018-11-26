from django.conf.urls import url

from repair.apps.targets import views

urlpatterns = [
    url(r'^$', views.TargetsIndexView.as_view(), name='index')
]


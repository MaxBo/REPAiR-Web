from django.conf.urls import url, include

from repair.apps.login import views

urlpatterns = [
    url(r'^', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^session', views.SessionView.as_view(), name='session')
]
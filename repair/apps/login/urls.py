from django.conf.urls import url

from repair.apps.login import views

urlpatterns = [
    url(r'^session', views.SessionView.as_view(), name='session')
]
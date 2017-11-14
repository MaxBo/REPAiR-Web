from django.conf.urls import url

from repair.apps.admin import views

urlpatterns = [
    url(r'^$', views.AdminView.as_view(), name='admin')
]
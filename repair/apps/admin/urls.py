from django.conf.urls import url

from repair.apps.admin import views

urlpatterns = [
    url(r'^$', views.index, name='admin')
]
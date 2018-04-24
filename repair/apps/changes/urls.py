from django.conf.urls import url

from repair.apps.changes import views

urlpatterns = [
    url(r'^$', views.ChangesIndexView.as_view(), name='index')

]
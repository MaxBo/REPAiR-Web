from django.conf.urls import url

from repair.apps.sq_flows import views

urlpatterns = [
    url(r'^$', views.index, name='sq-flows')
]
from django.conf.urls import url
from repair.apps.asmfa import views

urlpatterns = [
    url(r'^$', views.index, name='index'),

# ex: /flows/5/
url(r'^flows/(?P<id>[0-9]+)/$',
    views.flows,
    name='flows'),
]

from django.conf.urls import url

from repair.static.webhook import views

urlpatterns = [
    url(r'^$', views.payload, name='payload')
]
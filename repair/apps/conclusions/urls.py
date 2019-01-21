from django.conf.urls import url

from repair.apps.conclusions import views

urlpatterns = [
    url(r'^$', views.ConclusionsIndexView.as_view(), name='index'),
]

from django.conf.urls import url

from repair.apps.conclusions import views

urlpatterns = [
    url(r'^$', views.RecommendationsIndexView.as_view(), name='index'),
]

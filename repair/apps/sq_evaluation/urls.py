from django.conf.urls import url

from repair.apps.sq_evaluation import views

urlpatterns = [
    url(r'^$', views.index, name='sq-evaluation')
]
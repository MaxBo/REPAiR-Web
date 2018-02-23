from django.conf.urls import url

from repair.apps.studyarea import views

urlpatterns = [
    url(r'^$', views.StudyAreaIndexView.as_view(), name='index'),

]
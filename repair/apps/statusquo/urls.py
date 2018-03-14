from django.conf.urls import url

from repair.apps.statusquo import views

urlpatterns = [
    url(r'^$', views.statusquo.StatusQuoView.as_view(), name='status-quo')
]
from django.conf.urls import url, include

from repair.apps.login import views
from repair.apps.utils.views import SessionView

urlpatterns = [
    url(r'^', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^session', SessionView.as_view(), name='session')
]
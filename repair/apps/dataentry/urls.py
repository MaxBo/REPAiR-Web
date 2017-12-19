from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from repair.apps.dataentry import views

urlpatterns = [
    url(r'^$', login_required(views.DataEntryView.as_view()), name='data-entry')
]
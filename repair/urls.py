"""repair URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include

from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from repair.views import HomeView
from django.contrib.auth.views import logout


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^$', HomeView.as_view(), name='index'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^admin/', admin.site.urls),
    url(r'^data-entry/', include('repair.apps.dataentry.urls')),
    url(r'^study-area/', include('repair.apps.studyarea.urls')),
    url(r'^status-quo/', include('repair.apps.statusquo.urls')),
    url(r'^changes/', include('repair.apps.changes.urls')),
    url(r'^decisions/', include('repair.apps.decisions.urls')),
    url(r'^impacts/', include('repair.apps.impacts.urls')),
    # API urls
    url('^login/', include('repair.apps.login.urls')),
    url(r'^api/', include('repair.rest_urls')),
    url(r'^logout', logout, {'next_page': '/'}, name='logout')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

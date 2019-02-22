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
from repair.views import HomeView
from django.contrib.auth.views import logout
from repair.apps.login.views import (SessionView, LoginView,
                                     PasswordChangeView)
from django.views.i18n import JavaScriptCatalog
from django.views.generic import TemplateView
from repair.apps.wmsresources.views import (WMSProxyView)
from repair.apps import admin
#from django.contrib import admin


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^$', HomeView.as_view(), name='index'),
    url(r'^privacy/', TemplateView.as_view(
        template_name='about/privacy.html')),
    url(r'^disclaimer/', TemplateView.as_view(
        template_name='about/disclaimer.html')),
    url(r'^legal-notice/', TemplateView.as_view(
        template_name='about/legal.html')),
    url(r'^contact/', TemplateView.as_view(
        template_name='about/contact.html')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^admin/', admin.site.urls),
    url(r'^data-entry/', include('repair.apps.dataentry.urls')),
    url(r'^study-area/', include('repair.apps.studyarea.urls')),
    url(r'^status-quo/', include('repair.apps.statusquo.urls')),
    # API urls
    url(r'^login/', LoginView.as_view(template_name='login/login.html'),
        name='login'),
    url(r'^password/', PasswordChangeView.as_view(template_name='login/password_change_form.html'),
        name='password_change_form'),
    url(r'^password-done/', TemplateView.as_view(template_name='login/password_change_done.html'),
        name='password_change_done'),
    url(r'^session', SessionView.as_view(), name='session'),
    url(r'^logout', logout, {'next_page': '/'}, name='logout'),
    url(r'^api/', include('repair.rest_urls')),
    url(r'^publications/', include('publications_bootstrap.urls')),
    url(r'^jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    url(r'^proxy/layers/(?P<layer_id>[0-9]+)/wms', WMSProxyView.as_view(), name='wms_proxy'),
    url(r'^wms-client/', include('wms_client.urls'))
] \
+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

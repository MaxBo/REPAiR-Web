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
from rest_framework import routers
from repair.apps.login import views as login_views
from repair.apps.study_area.views import LinksViewSet, NodesViewSet

from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from django.conf.urls.static import static
from repair.apps.changes.views import (
                                       SolutionCategoriesListApiView,
                                       SolutionCategoryApiView,
                                       SolutionsListApiView,
                                       SolutionApiView,
                                       )

router = routers.DefaultRouter()
router.register(r'users', login_views.UserViewSet)
router.register(r'groups', login_views.GroupViewSet)
router.register(r'links', LinksViewSet)
router.register(r'nodes', NodesViewSet)


def index(request):
    template = loader.get_template('index.html')
    context = {}
    html = template.render(context, request)
    return HttpResponse(html)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^admin/', include('repair.apps.admin.urls')),
    url(r'^study-area/', include('repair.apps.study_area.urls')),
    url(r'^status-quo/', include('repair.apps.status_quo.urls')),
    url(r'^changes/', include('repair.apps.changes.urls')),
    url(r'^decisions/', include('repair.apps.decisions.urls')),
    url(r'^impacts/', include('repair.apps.impacts.urls')),
    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    #url(r'^api/payload', include('repair.static.webhook.urls')),
    # API urls
    url(r'^api/casestudy/(?P<casestudy_id>[0-9]+)/solutioncategories/$',
        SolutionCategoriesListApiView.as_view(),
        name='apisolutioncategories'),
    url(r'^api/casestudy/(?P<casestudy_id>[0-9]+)/solutioncategories/(?P<solution_category>[0-9]+)/$',
        SolutionCategoryApiView.as_view(),
        name='apisolutioncategory'),
    url(r'^api/casestudy/(?P<casestudy_id>[0-9]+)/solutioncategories/(?P<solution_category>[0-9]+)/solutions/$',
        SolutionsListApiView.as_view(),
        name='apisolutions'),
    url(r'^api/casestudy/(?P<casestudy_id>[0-9]+)/solutioncategories/(?P<solution_category>[0-9]+)/solutions/(?P<solution_id>[0-9]+)/$',
        SolutionApiView.as_view(),
        name='apisolution'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

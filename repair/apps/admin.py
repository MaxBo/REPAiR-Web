from django.contrib.admin import * 
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.decorators import register as dec_reg
from django.apps import apps
from django.http import HttpResponseForbidden
import numpy as np
from django.utils.translation import gettext as _

from repair.apps.login.models import Profile
from wms_client.models import WMSResource
from publications_bootstrap.models import Publication

def register(*models):
    return dec_reg(*models, site=site)


STAFF_ACCESS = [ Profile, WMSResource, Publication]


class Http403(Exception):
    pass


class RestrictedAdminSite(AdminSite):
    '''
    restricts admin site access for staff (not superuser) to models defined
    in staff_access
    '''
    def __init__(self):
        super().__init__()
        
        self.access_dict = {}
        # build a dict assigning the accessible models to their apps
        for model in STAFF_ACCESS:
            app_label = model._meta.app_label
            object_name = model._meta.object_name
            if app_label not in self.access_dict:
                self.access_dict[app_label] = []
            self.access_dict[app_label].append(object_name)
    
    def _build_app_dict(self, request, label=None):
        app_dict = super()._build_app_dict(request, label=label)
        
        if request.user.is_superuser or not app_dict:
            return app_dict
        
        # if label is passed, a single app is looked for
        if label is not None:
            if label in self.access_dict:
                return app_dict
            else:
                raise Http403(_('The requested admin page is '
                                'accessible by superusers only.'))

        # all apps are queried when the index site is requested
        permitted_app_dict = {}
        for app_label, object_names in self.access_dict.items():
            app = app_dict[app_label]
            permitted_app = app_dict[app_label]
            permitted_app['models'] = [m for m in app['models']
                                       if m['object_name'] in object_names]
            permitted_app_dict[app_label] = permitted_app
        return permitted_app_dict
    
    def app_index(self, request, app_label, extra_context=None):
        try:
            return super().app_index(request, app_label,
                                     extra_context=extra_context)
        except Http403 as e:
            return HttpResponseForbidden(str(e))

site = RestrictedAdminSite()


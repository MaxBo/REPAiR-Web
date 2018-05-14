from django.contrib.admin import * 
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.decorators import register as dec_reg
from repair.apps.login.models import Profile
from wms_client.models import WMSResource
from publications_bootstrap.models import Publication
from django.apps import apps
import numpy as np

def register(*models):
    return dec_reg(*models, site=site)


STAFF_ACCESS = [ Profile, WMSResource, Publication]


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
    
    def get_app_list(self, request):
        full_app_list = super().get_app_list(request)
        if request.user.is_superuser:
            return full_app_list
        
        permitted_app_list = []
        for app in full_app_list:
            accessible = self.access_dict.get(app['app_label'])
            if not accessible:
                continue
            permitted_app = app.copy()
            permitted_app['models'] = [m for m in app['models']
                                       if m['object_name'] in accessible]
            permitted_app_list.append(permitted_app)
        return permitted_app_list

    def has_permission(self, request):
        if request.user.is_superuser:
            return super().has_permission(request)
        
        url = request.path.split(self.name)[1]
        # admin base path is accessible for staff
        if url == '/':
            return True
        
        permitted_apps = self.get_app_list(request)
        # look for label 
        for app_label in self.access_dict:
            if url.startswith('/' + app_label):
                return True
        return False

site = RestrictedAdminSite()


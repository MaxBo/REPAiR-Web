from django.contrib.admin import * 
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.decorators import register as dec_reg

def register(*models):
    return dec_reg(*models, site=site)


class RestrictedAdminSite(AdminSite):
    '''
    restricts admin site access for staff (not superuser) to apps defined
    in self.staff_access
    '''
    staff_access = ['Publications_Bootstrap', 'Wms_Client']
    def get_app_list(self, request):
        full_app_list = super().get_app_list(request)
        if request.user.is_superuser:
            return full_app_list
        permitted_app_list = [app for app in full_app_list if app['name'] in self.staff_access]
        return permitted_app_list

    
    #def has_permission(self, request):
        #"""
        #Return True if the given HttpRequest has permission to view
        #*at least one* page in the admin site.
        #"""
        #return request.user.is_active and request.user.is_superuser

site = RestrictedAdminSite()


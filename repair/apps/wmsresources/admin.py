# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from repair.apps import admin

from reversion_compare.admin import CompareVersionAdmin as VersionAdmin

from wms_client.models import WMSResource
from wms_client.admin import WMSResourceAdmin

from .models import WMSResourceInCasestudy, CaseStudy


class WMSResourceInCasestudyInline(admin.StackedInline):
    model = WMSResourceInCasestudy
    can_delete = False
    verbose_name_plural = 'WMSResourceInCasestudies'
    fk_name = 'wmsresource'


class CustomWMSResourceAdmin(VersionAdmin, WMSResourceAdmin):
    inlines = WMSResourceAdmin.inlines + [WMSResourceInCasestudyInline]

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        obj.save()
        casestudy_id = request.session.get('casestudy', None)
        if casestudy_id is not None:
            casestudy = CaseStudy.objects.get(pk=casestudy_id)
            wic = WMSResourceInCasestudy.objects.get_or_create(
                casestudy=casestudy,
                wmsresource=obj)

            
try:
    admin.site.unregister(WMSResource)
except:
    pass
admin.site.register(WMSResource, CustomWMSResourceAdmin)

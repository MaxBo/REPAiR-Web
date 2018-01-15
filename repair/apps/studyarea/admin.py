# -*- coding: utf-8 -*-
from django.contrib import admin
from . import models


#class CasestudyInline(admin.StackedInline):
    #model = models.Profile.casestudies.through


@admin.register(models.Area)
class AreaAdmin(admin.ModelAdmin):
    """"""

    #list_display = ('name', "get_casestudies", "organization")
    ##inlines = (CasestudyInline, )

    #search_fields = ["user__username"]

@admin.register(models.AdminLevels)
class AdminLevelsAdmin(admin.ModelAdmin):
    """"""

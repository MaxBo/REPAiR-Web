# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from repair.apps import admin
from django.conf.urls import url
from django.http import HttpResponseRedirect

from reversion_compare.admin import CompareVersionAdmin as VersionAdmin

from publications_bootstrap.models import Publication
from publications_bootstrap.admin import PublicationAdmin
from publications_bootstrap.admin_views.import_bibtex import (
    parse_upload_bibtex, get_response)

from .models import PublicationInCasestudy, CaseStudy


def import_bibtex(request):
    if request.method == 'POST':
        # try to import BibTex
        publications = parse_upload_bibtex(request)

        # create the entries in publication_in_casestudy
        casestudy_id = request.session.get('casestudy', None)
        if casestudy_id is not None:
            casestudy = CaseStudy.objects.get(pk=casestudy_id)
            for publication in publications:
                pic = PublicationInCasestudy.objects.get_or_create(
                    casestudy=casestudy,
                    publication=publication)

        # redirect to publication listing
        return HttpResponseRedirect('../')
    else:
        response = get_response(request)
        return response


class PublicationInCasestudyInline(admin.StackedInline):
    model = PublicationInCasestudy
    can_delete = False
    verbose_name_plural = 'PublicationInCasestudies'
    fk_name = 'publication'


class CustomPublicationAdmin(VersionAdmin, PublicationAdmin):
    inlines = PublicationAdmin.inlines + [PublicationInCasestudyInline]
    change_list_template = 'publications/publication_change_list.html'

    def get_urls(self):
        urls = [url(r'^import_bibtex/$',
                    import_bibtex,
                    name='publications_publication_import_bibtex'),
                ] + super().get_urls()
        return urls

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        obj.save()
        casestudy_id = request.session.get('casestudy', None)
        if casestudy_id is not None:
            casestudy = CaseStudy.objects.get(pk=casestudy_id)
            pic = PublicationInCasestudy.objects.get_or_create(
                casestudy=casestudy,
                publication=obj)

try:
    admin.site.unregister(Publication)
except:
    pass
admin.site.register(Publication, CustomPublicationAdmin)

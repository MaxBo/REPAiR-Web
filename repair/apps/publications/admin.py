# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.conf.urls import url
from django.http import HttpResponseRedirect

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

class CustomPublicationAdmin(PublicationAdmin):
    inlines = (PublicationInCasestudyInline, )

    def get_urls(self):
        return [url(r'^import_bibtex/$',
                    import_bibtex,
                    name='publications_publication_import_bibtex'),
                ] + super().get_urls()


admin.site.unregister(Publication)
admin.site.register(Publication, CustomPublicationAdmin)
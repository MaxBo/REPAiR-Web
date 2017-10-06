from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView
from django.utils.translation import ugettext as _
from rest_framework import viewsets

import numpy as np

def stakeholders(request):
    template = loader.get_template('study_area/stakeholders.html')
    context = {}
    html = template.render(context, request)
    return HttpResponse(html)
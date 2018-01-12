from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView

from repair.views import BaseView

class DecisionsIndexView(BaseView):
    template_name = "decisions/index.html"
from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView
from repair.views import BaseView

class ImpactsIndexView(BaseView):
    template_name = "impacts/index.html"
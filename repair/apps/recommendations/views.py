from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView
from repair.views import BaseView

class RecommendationsIndexView(BaseView):
    template_name = "recommendations/index.html"

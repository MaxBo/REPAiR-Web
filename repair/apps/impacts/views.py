from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView

def index(request):
    template = loader.get_template('impacts/index.html')
    context = {}
    html = template.render(context, request)
    return HttpResponse(html)
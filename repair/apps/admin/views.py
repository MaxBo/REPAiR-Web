from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView
from plotly.offline import iplot
import urllib
import json
from plotly import offline
from plotly.graph_objs import Figure, Data, Layout
from repair.apps.login.models import CaseStudy
from repair.apps.asmfa.models import Material
from repair.views import BaseView


class AdminView(BaseView): 
    template_name = "admin/index.html"
    title = 'Admin Area'
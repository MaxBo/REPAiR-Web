from django.views.generic import TemplateView
from repair.apps.login.models import CaseStudy


class BaseView(TemplateView):

    def casestudies(self):
        return CaseStudy.objects.all()


class HomeView(BaseView):
    template_name = "index.html"
    title = 'Welcome'
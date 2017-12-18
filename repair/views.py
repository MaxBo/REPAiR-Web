from django.views.generic import TemplateView
from repair.apps.login.models import CaseStudy


class BaseView(TemplateView):
    
    def get(self, request, *args, **kwargs):

        if 'casestudy' not in request.session:
            request.session['casestudy'] = None
        return super().get(request, *args, **kwargs)

    def casestudies(self):
        return CaseStudy.objects.all()


class HomeView(BaseView):
    template_name = "index.html"
    title = 'Welcome'
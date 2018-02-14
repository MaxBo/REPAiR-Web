from django.views.generic import TemplateView
from repair.apps.login.models import CaseStudy


class BaseView(TemplateView):
    
    def get(self, request, *args, **kwargs):

        if 'casestudy' not in request.session:
            request.session['casestudy'] = None
        if 'mode' not in request.session:
            request.session['mode'] = 0
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        kwargs['casestudies'] = self.casestudies()
        return kwargs

    def casestudies(self):
        user_id = self.request.user.id or -1
        casestudies = set()
        for casestudy in CaseStudy.objects.all():
            if len(casestudy.userincasestudy_set.all().filter(user__id=user_id)):
                casestudies.add(casestudy)
        return casestudies


class HomeView(BaseView):
    template_name = "index.html"
    title = 'Welcome'
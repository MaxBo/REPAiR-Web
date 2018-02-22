from django.views.generic import TemplateView
from django.core.exceptions import ObjectDoesNotExist
from repair.apps.login.models import CaseStudy


class BaseView(TemplateView):
    modes = { 0: 'Workshop', 1: 'Setup'}

    def get(self, request, *args, **kwargs):
        if 'casestudy' not in request.session:
            request.session['casestudy'] = None
        if 'mode' not in request.session:
            request.session['mode'] = 0
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        casestudy_id = self.request.session.get('casestudy', 0)
        try:
            casestudy = CaseStudy.objects.get(pk=casestudy_id)
        except ObjectDoesNotExist:
            casestudy = None
        
        mode = self.request.session.get('mode', 0)
        
        kwargs['mode'] = self.modes[mode]
        kwargs['casestudy'] = casestudy
        kwargs['casestudies'] = self.casestudies()
        return kwargs

    def casestudies(self):
        user_id = self.request.user.id or -1
        casestudies = set()
        for casestudy in CaseStudy.objects.all():
            if len(casestudy.userincasestudy_set.all().filter(user__id=user_id)):
                casestudies.add(casestudy)
        return casestudies


class ModeView(BaseView):
    
    def get(self, request, *args, **kwargs):
        mode = request.session.get('mode', 0)
        if mode == 1:
            return self.render_setup(request)
        else:
            return self.render_workshop(request)
    
    def render_setup(self, request, *args, **kwargs):
        raise NotImplementedError

    def render_workshop(self, request, *args, **kwargs):
        raise NotImplementedError


class HomeView(BaseView):
    template_name = "index.html"
    title = 'Welcome'
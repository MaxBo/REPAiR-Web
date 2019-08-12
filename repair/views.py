from django.views.generic import TemplateView
from django.core.exceptions import ObjectDoesNotExist
from repair.apps.login.models import CaseStudy
from django.shortcuts import render
from django.contrib.auth.models import Permission, User, Group


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
        kwargs['data_entry_permitted'] = self.data_entry_permitted()
        kwargs['conclusions_permitted'] = self.conclusions_permitted()
        return kwargs

    def casestudies(self):
        user_id = self.request.user.id or -1
        casestudies = set()
        for casestudy in CaseStudy.objects.all():
            if len(casestudy.userincasestudy_set.all().filter(user__id=user_id)):
                casestudies.add(casestudy)
        return casestudies

    def setup_mode_permitted(self):
        return ('login.setupmode_casestudy' in
                self.request.user.get_all_permissions())

    def data_entry_permitted(self):
        return ('login.dataentry_casestudy' in
                self.request.user.get_all_permissions())

    def conclusions_permitted(self):
        return ('login.conclusions_casestudy' in
                self.request.user.get_all_permissions())


class ModeView(BaseView):

    def get(self, request, *args, **kwargs):
        if 'mode' in request.GET:
            mode = request.GET.get('mode')
            mode = 1 if mode == 'setup' else 0
            request.session['mode'] = mode

        mode = request.session.get('mode', 0)

        # all pages with modes require a casestudy to be selected
        if not request.session.get('casestudy', None):
            return render(request, 'casestudy-missing.html',
                          self.get_context_data())

        if mode == 1:
            return self.render_setup(request)
        else:
            return self.render_workshop(request)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs['setup_mode_permitted'] = self.setup_mode_permitted()
        return kwargs

    def render_setup(self, request, *args, **kwargs):
        raise NotImplementedError

    def render_workshop(self, request, *args, **kwargs):
        raise NotImplementedError


class HomeView(BaseView):
    template_name = "index.html"
    title = 'Welcome'

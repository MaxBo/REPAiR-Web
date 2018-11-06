from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin

from repair.views import ModeView
from repair.apps.asmfa.models import KeyflowInCasestudy


class StrategyIndexView(LoginRequiredMixin, ModeView):

    def render_setup(self, request):
        casestudy = request.session.get('casestudy')
        keyflows = KeyflowInCasestudy.objects.filter(casestudy=casestudy)
        context = self.get_context_data()
        context['keyflows'] = keyflows

        return render(request, 'strategy/index.html', context)

    def render_workshop(self, request):
        # same entry point as in setup mode
        return self.render_setup(request)

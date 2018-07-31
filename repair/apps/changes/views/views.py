from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin

from repair.views import ModeView


class ChangesIndexView(LoginRequiredMixin, ModeView):

    def render_setup(self, request):
        return render(request, 'changes/index.html',
                      self.get_context_data())

    def render_workshop(self, request):
        # same entry point as in setup mode
        return self.render_setup(request)

from django.http import HttpResponse
from django.template import loader
from rest_framework import viewsets
from repair.views import ModeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
import numpy as np
from repair.apps.login.views import  CasestudyViewSetMixin
from repair.apps.utils.views import (ModelPermissionViewSet,
                                     ReadUpdatePermissionViewSet)


class StatusQuoView(LoginRequiredMixin, ModeView):
    def render_setup(self, request):
        return render(request, 'statusquo/index.html',
                      self.get_context_data())

    def render_workshop(self, request):
        # same entry point as in setup mode
        return self.render_setup(request)
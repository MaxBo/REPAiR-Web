from django.http import HttpResponse
from django.template import loader
from rest_framework import viewsets
from repair.views import ModeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
import numpy as np
from repair.apps.asmfa.models import KeyflowInCasestudy
from repair.apps.utils.views import (CasestudyViewSetMixin, 
                                     ModelPermissionViewSet,
                                     ReadUpdatePermissionViewSet)


class StatusQuoView(LoginRequiredMixin, ModeView):
    def render_setup(self, request):
        casestudy = request.session.get('casestudy')
        keyflows = KeyflowInCasestudy.objects.filter(casestudy=casestudy)
        
        context = self.get_context_data()

        context['keyflows'] = keyflows
        return render(request, 'statusquo/index.html',
                      context)

    def render_workshop(self, request):
        # same entry point as in setup mode
        return self.render_setup(request)
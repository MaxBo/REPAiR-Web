from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render

from repair.apps.studyarea.models import (StakeholderCategory,
                                          Stakeholder,
                                          )
from repair.apps.login.models import CaseStudy
from repair.apps.changes.forms import NameForm
from .graphs import Testgraph1, Testgraph2
from django.contrib.auth.mixins import LoginRequiredMixin

from repair.views import BaseView, ModeView


class StudyAreaIndexView(LoginRequiredMixin, ModeView):

    def render_setup(self, request):
        return render(request, 'studyarea/index.html',
                      self.get_context_data())
    
    def render_workshop(self, request):
        return render(request, 'studyarea/index.html',
                      self.get_context_data())

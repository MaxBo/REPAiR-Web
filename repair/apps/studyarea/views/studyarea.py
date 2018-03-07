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
        return render(request, 'studyarea/setup/index.html',
                      self.get_context_data())
    
    def render_workshop(self, request):
        context = self.get_context_data()
        
        casestudy_id = context['casestudy'].id
        stakeholder_category_list = \
            StakeholderCategory.objects.filter(casestudy=casestudy_id)
        stakeholder_list = Stakeholder.objects.filter(
            stakeholder_category__casestudy=casestudy_id)
        
        context['stakeholder_category_list'] = stakeholder_category_list
        context['stakeholder_list'] = stakeholder_list
        context['graph1'] = Testgraph1().get_context_data()
        context['graph2'] = Testgraph2().get_context_data()
        return render(request, 'studyarea/workshop/index.html', context)


class StakeholderCategoriesView(BaseView):

    def get(self, request, stakeholdercategory_id):
        casestudy_id = request.session.get('casestudy', 0)
        casestudy = CaseStudy.objects.get(pk=casestudy_id)
        stakeholder_category = StakeholderCategory.objects.get(
            pk=stakeholdercategory_id)
        stakeholders = stakeholder_category.stakeholder_set.all()
        context = {'stakeholder_category': stakeholder_category,
                   'stakeholders': stakeholders,
                   'casestudy': casestudy,
                   }
        context['casestudies'] = self.casestudies()
        return render(request, 'changes/stakeholder_category.html', context)


class StakeholderView(BaseView):
    def get(self, request, stakeholder_id):
        stakeholder = Stakeholder.objects.get(pk=stakeholder_id)
        if request.method == 'POST':
            form = NameForm(request.POST)
            if form.is_valid():
                stakeholder.name = form.cleaned_data['name']
                stakeholder.full_clean()
                stakeholder.save()
                return HttpResponseRedirect(
                    '/changes/stakeholdercategories/{}'.
                    format(stakeholder.stakeholder_category.id))
        context = {'stakeholder': stakeholder,
                   }
        context['casestudies'] = self.casestudies()
        return render(request, 'changes/stakeholder.html', context)

from django.http import HttpResponseRedirect

from django.shortcuts import render

from repair.apps.studyarea.models import (StakeholderCategory,
                                          Stakeholder,
                                          )
from repair.apps.login.models import CaseStudy, Profile
from repair.apps.changes.forms import NameForm
from .graphs import Testgraph1, Testgraph2

from repair.views import BaseView


class StudyAreaIndexView(BaseView):

    def get(self, request):
        casestudy_list = CaseStudy.objects.order_by('id')[:20]
        users = Profile.objects.order_by('id')[:20]

        # get the current casestudy
        url_pks = request.session.get('url_pks', {})
        casestudy = url_pks.get('casestudy_pk')
        if casestudy:
            stakeholder_category_list = \
                StakeholderCategory.objects.filter(casestudy=casestudy)
        else:
            stakeholder_category_list = StakeholderCategory.objects.all()

        context = {'casestudy_list': casestudy_list,
                   'users': users,
                   'stakeholder_category_list': stakeholder_category_list,
                   }

        context['graph1'] = Testgraph1().get_context_data()
        context['graph2'] = Testgraph2().get_context_data()
        context['casestudies'] = self.casestudies()
        return render(request, 'studyarea/index.html', context)


class StakeholderCategoriesView(BaseView):

    def get(self, request, stakeholdercategory_id):
        stakeholder_category = StakeholderCategory.objects.get(
            pk=stakeholdercategory_id)
        stakeholders = stakeholder_category.stakeholder_set.all()
        context = {'stakeholder_category': stakeholder_category,
                   'stakeholders': stakeholders,
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

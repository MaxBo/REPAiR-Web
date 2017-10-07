from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView
from django.shortcuts import render

from django.utils.translation import ugettext as _
from rest_framework import viewsets
from repair.apps.changes.models import (CaseStudy,
                                        Unit,
                                        UserAP12,
                                        UserAP34,
                                        StakeholderCategory,
                                        Stakeholder,
                                        SolutionCategory,
                                        Solution)

from repair.apps.changes.serializers import (CaseStudySerializer,
                                             StakeholderCategorySerializer,
                                             StakeholderSerializer,
                                             )



class CaseStudyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = CaseStudy.objects.all()
    serializer_class = CaseStudySerializer


class StakeholderCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = StakeholderCategory.objects.all()
    serializer_class = StakeholderCategorySerializer


class StakeholderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Stakeholder.objects.all()
    serializer_class = StakeholderSerializer


def index(request):
    casestudy_list = CaseStudy.objects.order_by('id')[:10]
    context = {'casestudy_list': casestudy_list}
    return render(request, 'changes/index.html', context)

def casestudy(request, casestudy_id):
    casestudy = CaseStudy.objects.get(pk=casestudy_id)
    stakeholder_categories = StakeholderCategory.objects.filter(case_study_id=casestudy_id)

    context = {'casestudy': casestudy,
               'stakeholder_categories': stakeholder_categories,
               }
    return render(request, 'changes/stakeholder_categories.html', context)

def stakeholder_categories(request, casestudy_id, stakeholder_category_id):
    casestudy = CaseStudy.objects.get(pk=casestudy_id)
    stakeholder_category = StakeholderCategory.objects.get(pk=stakeholder_category_id)
    stakeholders = Stakeholder.objects.filter(
        stakeholder_category_id=stakeholder_category_id)
    context = {'casestudy': casestudy,
               'stakeholder_category': stakeholder_category,
               'stakeholders': stakeholders,
               }
    return render(request, 'changes/stakeholders.html', context)

def stakeholders(request, stakeholder_id):
    stakeholder = Stakeholder.get(pk=stakeholder_id)
    return HttpResponse('Stakeholder {.id}: {.name}'.format(stakeholder))

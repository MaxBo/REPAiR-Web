from django.http import HttpResponse
from django.template import loader
from django.views.generic import TemplateView

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

from repair.apps.changes.serializers import CaseStudySerializer



class CaseStudyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = CaseStudy.objects.all()
    serializer_class = CaseStudySerializer




#def index(request):
    #template = loader.get_template('case_study/index.html')
    #context = {}
    #html = template.render(context, request)
    #return HttpResponse(html)

#def stakeholders(request):
    #template = loader.get_template('study_area/stakeholders.html')
    #context = {}
    #html = template.render(context, request)
    #return HttpResponse(html)
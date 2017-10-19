# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from repair.apps.asmfa.models import Activity, Flow, Activity2Activity
from repair.apps.asmfa.forms import QualityChoice


def index(request):
    activities = Activity.objects.order_by('nace')
    flows = Activity2Activity.objects.order_by('id')
    context = {'activities': activities, 'flows': flows}
    return render(request, 'asmfa/index.html', context)


def flows(request, id):
    flow = Activity2Activity.objects.get(pk=id)
    if request.method == 'POST':
        form = QualityChoice(request.POST)
        if form.is_valid():
            flow.quality = form.cleaned_data['choice_field']
            flow.full_clean()
            flow.save()
            return HttpResponseRedirect('/asmfa/index')
    context = {'flows': flows,
               }
    return render(request, 'asmfa/flows.html', context)

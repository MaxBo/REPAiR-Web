from repair.apps.studyarea.models import (StakeholderCategory,
                                          Stakeholder,
                                          )
from repair.apps.login.models import CaseStudy
from repair.apps.login.serializers import CaseStudySerializer
from rest_framework import serializers


class StakeholderSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Stakeholder
        fields = ('id', 'name', 'stakeholder_category')


class StakeholderCategorySerializer(serializers.HyperlinkedModelSerializer):
    def __init__(self, *args, **kwargs):
        request = kwargs.get('context', {}).get('request')
        casestudy = request.session.get('casestudy')
        if casestudy:
            self.fields['casestudy'].queryset = CaseStudy.objects.filter(id=casestudy)
        super().__init__(*args, **kwargs)

    class Meta:
        model = StakeholderCategory
        fields = ('id', 'casestudy', 'name')


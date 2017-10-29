from repair.apps.studyarea.models import (StakeholderCategory,
                                          Stakeholder,
                                          )
from repair.apps.login.models import CaseStudy
from repair.apps.login.serializers import CaseStudySerializer
from rest_framework import serializers


class StakeholderSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Stakeholder
        fields = ('url', 'id', 'name', 'stakeholder_category')


class StakeholderOfCasestudyField(serializers.HyperlinkedRelatedField):
    def get_queryset(self):
        obj = self.root.instance
        #request = self.context.get('request')
        #casestudy = request.session.get('casestudy')
        if obj:
            queryset = Stakeholder.objects.filter(
                stakeholder_category__casestudy=obj.casestudy.id)
        else:
            queryset = Stakeholder.objects.all()
        return queryset


class StakeholderCategorySerializer(serializers.HyperlinkedModelSerializer):
    #def __init__(self, *args, **kwargs):
        #request = kwargs.get('context', {}).get('request')
        #casestudy = request.session.get('casestudy')
        #if casestudy:
            #self.fields['casestudy'].queryset = CaseStudy.objects.filter(id=casestudy)
        #super().__init__(*args, **kwargs)
    stakeholder_set = StakeholderOfCasestudyField(
        many=True,
        #queryset=Stakeholder.objects.filter(stakeholder_category__casestudy=5),
        view_name='stakeholder-detail')
    class Meta:
        model = StakeholderCategory
        fields = ('url', 'id', 'casestudy', 'name',
                  'stakeholder_set',
                  )


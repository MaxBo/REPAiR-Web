from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer

from repair.apps.studyarea.models import (StakeholderCategory,
                                          Stakeholder,
                                          )
from repair.apps.login.models import CaseStudy
from repair.apps.login.serializers import (CaseStudySerializer,
                                           InCasestudyField,
                                           InCaseStudyIdentityField,
                                           IdentityFieldMixin,
                                           CreateWithUserInCasestudyMixin)



class StakeholderCategoryField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}


class StakeholderSetField(InCasestudyField):
    lookup_url_kwarg = 'stakeholdercategory_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'stakeholder_category__casestudy__id',
                            'stakeholdercategory_pk': 'stakeholder_category__id', }


class StakeholderListField(IdentityFieldMixin, StakeholderSetField):
    """"""
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id',
                            'stakeholdercategory_pk': 'id', }


class StakeholderSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'stakeholder_category__casestudy__id',
        'stakeholdercategory_pk': 'stakeholder_category__id',
    }
    stakeholder_category = StakeholderCategoryField(
        view_name='stakeholdercategory-detail'
    )

    class Meta:
        model = Stakeholder
        fields = ('url', 'id', 'name', 'stakeholder_category')


class StakeholderSetSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'stakeholder_category__casestudy__id',
        'stakeholdercategory_pk': 'stakeholder_category__id',
    }
    class Meta:
        model = Stakeholder
        fields = ('url', 'id', 'name')


class StakeholderCategorySerializer(CreateWithUserInCasestudyMixin,
                                    NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    stakeholder_set = StakeholderListField(
        view_name='stakeholder-list')
    stakeholder_list = StakeholderSetField(source='stakeholder_set',
                                            many=True,
                                            view_name='stakeholder-detail')

    class Meta:
        model = StakeholderCategory
        fields = ('url', 'id', 'name', 'stakeholder_set', 'stakeholder_list',
                  )

    def get_required_fields(self, user):
        required_fields = {'casestudy': user.casestudy,}
        return required_fields
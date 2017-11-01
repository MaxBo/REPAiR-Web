from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

from repair.apps.login.models import CaseStudy
from repair.apps.asmfa.models import (ActivityGroup,
                                      Activity,
                                      Actor,
                                      Flow,
                                      Actor2Actor,
                                      Activity2Activity,
                                      Group2Group,
                                      Material,
                                      Quality,
                                      MaterialInCasestudy)
from repair.apps.login.serializers import (NestedHyperlinkedModelSerializer2)


class MaterialSerializer(NestedHyperlinkedModelSerializer2):
    parent_lookup_kwargs = {}
    casestudies = serializers.HyperlinkedRelatedField(
        queryset = CaseStudy.objects.all(),
        #source='casestudies',
        many=True,
        view_name='casestudy-detail',
        help_text=_('Select the Casestudies the material is used in')
    )

    class Meta:
        model = Material
        fields = ('url', 'id', 'code', 'name', 'casestudies')


    def update(self, obj, validated_data):
        """update the user-attributes, including profile information"""
        material = obj

        # handle groups
        new_casestudies = validated_data.pop('casestudies', None)
        if new_casestudies is not None:
            MaterialInCasestudy = Material.casestudies.through
            casestudy_qs = MaterialInCasestudy.objects.filter(material=material.id)
            # delete existing groups
            casestudy_qs.exclude(casestudy__id__in=(cs.id for cs in new_casestudies)).delete()
            # add or update new groups
            for cs in new_casestudies:
                MaterialInCasestudy.objects.update_or_create(material=material,
                                                             casestudy=cs)

        # update other attributes
        obj.__dict__.update(**validated_data)
        obj.save()
        return obj

    def create(self, validated_data):
        """Create a new material"""
        code = validated_data.pop('code')

        material = Material.objects.create(code=code)
        self.update(obj=material, validated_data=validated_data)
        return material


class QualitySerializer(NestedHyperlinkedModelSerializer2):
    parent_lookup_kwargs = {}

    class Meta:
        model = Quality
        fields = ('url', 'id', 'name')


class MaterialInCasestudySerializer(NestedHyperlinkedModelSerializer2):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    note = serializers.CharField(required=False, allow_blank=True)
    material = serializers.HyperlinkedIdentityField(
        source='material',
        view_name='material-detail',
    )
    class Meta:
        model = MaterialInCasestudy
        fields = ('url', 'id',  'material', 'note')



class ActivityGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityGroup
        fields = ('code', 'name')


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ('id', 'nace', 'name', 'own_activitygroup')


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ('BvDid', 'name', 'consCode', 'year', 'revenue',
                  'employees', 'BvDii', 'website', 'own_activity')


class ActorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ('BvDid', 'name', 'own_activity')


class FlowSerializer(serializers.ModelSerializer):
    """Abstract Base Class for a Flow Serializer"""
    class Meta:
        model = Flow
        fields = ('id', 'material', 'amount', 'quality', 'origin',
                  'destination', 'casestudy')


class Actor2ActorSerializer(FlowSerializer):
    class Meta(FlowSerializer.Meta):
        model = Actor2Actor


class Activity2ActivitySerializer(FlowSerializer):
    class Meta(FlowSerializer.Meta):
        model = Activity2Activity


class Group2GroupSerializer(FlowSerializer):
    class Meta(FlowSerializer.Meta):
        model = Group2Group

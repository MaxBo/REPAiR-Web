from repair.apps.changes.models import (Unit,
                                        SolutionCategory,
                                        Solution,
                                        Implementation,
                                        SolutionInImplementation,
                                        )


from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from rest_framework_nested.relations import NestedHyperlinkedRelatedField


class NHRF(NestedHyperlinkedRelatedField):
    """This is fixed in rest_framework_nested, but not yet available on pypi"""
    def use_pk_only_optimization(self):
        return False


class SolutionInImplementationField(serializers.HyperlinkedRelatedField):
    def get_queryset(self):
        obj = self.root.instance
        if obj:
            implementations_qs = Implementation.objects.filter(
                user=obj.user.id)
        else:
            implementations_qs = Implementation.objects.all()
        return implementations_qs


class SolutionSerializer(NestedHyperlinkedModelSerializer):
    #implementation_set = SolutionInImplementationField(
        #many=True,
        #view_name='implementation_set_detail')
    parent_lookup_kwargs = {
        'casestudy_pk': 'solution_category__casestudy__id',
        'solutioncategory_pk': 'solution_category__id',
    }

    class Meta:
        model = Solution
        fields = ('url', 'id', 'name', 'user', 'description',
                  'one_unit_equals',
                  #'implementation_set',
                  )


class SolutionPostSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Solution
        fields = ('url', 'id', 'name', 'user', 'description', 'one_unit_equals',
                  'solution_category')


class SolutionSetSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'solutioncategory_pk': 'solution_category__id',
                            'casestudy_pk': 'solution_category__casestudy__id',}
    class Meta:
        model = Solution
        fields = ('url', 'id', 'name')


class SolutionCategorySerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    solution_set = SolutionSetSerializer(many=True, read_only=True)
    class Meta:
        model = SolutionCategory
        fields = ('url', 'id', 'name', 'user', 'solution_set')

    #def __init__(self, *args, **kwargs):
        #super().__init__(*args, **kwargs)
        ## get the request from parent serializer's context
        #request_obj = self.context.get('request')
        ## assign request object to nested serializer context
        #self.fields['solution_set'].context['request'] = request_obj


class SolutionCategoryPostSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = SolutionCategory
        fields = ('url', 'id', 'name', 'user')


from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from repair.apps.changes.models import (Unit,
                                        SolutionCategory,
                                        Solution,
                                        Implementation,
                                        SolutionInImplementation,
                                        UserInCasestudy,
                                        SolutionQuantity,
                                        SolutionRatioOneUnit,
                                        SolutionInImplementationNote,
                                        SolutionInImplementationQuantity,
                                        SolutionInImplementationGeometry,
                                        )

from repair.apps.login.serializers import (UserInCasestudySerializer,
                                           UserInCasestudyField,
                                           InCasestudyField,
                                           InCaseStudyIdentityField,
                                           IdentityFieldMixin,
                                           CreateWithUserInCasestudyMixin)



class UnitSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Unit
        fields = ('url', 'id', 'name')


class SolutionCategoryField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}


class SolutionField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk':
                            'solution_category__user__casestudy__id',
                            'solutioncategory_pk': 'solution_category__id',}



class SolutionSetField(InCasestudyField):
    """Returns a List of links to the solutions"""
    lookup_url_kwarg = 'solutioncategory_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'solution_category__user__casestudy__id',
                            'solutioncategory_pk': 'solution_category__id', }


class SolutionListField(IdentityFieldMixin, SolutionSetField):
    """Returns a Link to the solutions--list view"""
    lookup_url_kwarg = 'solutioncategory_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'solutioncategory_pk': 'id', }


class SolutionSetSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'solutioncategory_pk': 'solution_category__id',
                            'casestudy_pk':
                            'solution_category__user__casestudy__id',}
    class Meta:
        model = Solution
        fields = ('url', 'id', 'name')


class UnitField(serializers.HyperlinkedRelatedField):
    """A Unit Field"""


class SolutionCategorySerializer(CreateWithUserInCasestudyMixin,
                                 NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}
    solution_set = SolutionListField(
        view_name='solution-list')
    solution_list = SolutionSetField(
        source='solution_set',
        view_name='solution-detail',
        many=True
    )
    user = UserInCasestudyField(
        view_name='userincasestudy-detail',
    )

    class Meta:
        model = SolutionCategory
        fields = ('url', 'id', 'name', 'user', 'solution_set', 'solution_list')
        read_only_fields = ('url', 'id')


class SolutionDetailCreateMixin:
    def create(self, validated_data):
        """Create a new solution quantity"""
        casestudy_pk = self.context['request'].session['casestudy_pk']
        solution = Solution.objects.get(id=casestudy_pk['solution_pk'])

        obj = self.Meta.model.objects.create(
            solution=solution,
            **validated_data)
        return obj


class SolutionQuantitySerializer(SolutionDetailCreateMixin,
                                 #CreateWithUserInCasestudyMixin,
                                 NestedHyperlinkedModelSerializer):
    unit = UnitField(queryset=Unit.objects.all(), view_name='unit-detail')
    solution = SolutionField(view_name='solution-detail', read_only=True)
    parent_lookup_kwargs = {
        'casestudy_pk': 'solution__user__casestudy__id',
        'solutioncategory_pk': 'solution__solution_category__id',
        'solution_pk': 'solution__id',
    }
    class Meta:
        model = SolutionQuantity
        fields = ('url', 'id', 'name', 'unit', 'solution')



class SolutionDetailListField(InCaseStudyIdentityField):
    lookup_url_kwarg = 'solution_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'solutioncategory_pk': 'solution_category__id',
                            'solution_pk': 'id',
                            }


class SolutionRatioOneUnitSerializer(SolutionDetailCreateMixin,
                                     NestedHyperlinkedModelSerializer):
    unit = UnitField(queryset=Unit.objects.all(), view_name='unit-detail')
    solution = SolutionField(view_name='solution-detail', read_only=True)
    value = serializers.DecimalField(max_digits=10, decimal_places=3)
    parent_lookup_kwargs = {
        'casestudy_pk': 'solution__user__casestudy__id',
        'solutioncategory_pk': 'solution__solution_category__id',
        'solution_pk': 'solution__id',
    }
    class Meta:
        model = SolutionRatioOneUnit
        fields = ('url', 'id', 'name', 'value', 'unit', 'solution')



class SolutionSerializer(CreateWithUserInCasestudyMixin,
                         NestedHyperlinkedModelSerializer):

    parent_lookup_kwargs = {
        'casestudy_pk': 'user__casestudy__id',
        'solutioncategory_pk': 'solution_category__id',
    }
    user = UserInCasestudyField(view_name='userincasestudy-detail')
    solution_category = SolutionCategoryField(
        view_name='solutioncategory-detail')
    solutionquantity_set = SolutionDetailListField(
        view_name='solutionquantity-list')
    solutionratiooneunit_set = SolutionDetailListField(
        view_name='solutionratiooneunit-list')

    class Meta:
        model = Solution
        fields = ('url', 'id', 'name', 'user', 'description',
                  'one_unit_equals', 'solution_category',
                  'solutionquantity_set',
                  'solutionratiooneunit_set',
                  #'implementation_set',
                  )
        read_only_fields = ('url', 'id', )


class SolutionInImplementationSetField(InCasestudyField):
    """Returns a list of links to the solutions"""
    lookup_url_kwarg = 'implementation_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'implementation__user__casestudy__id',
                            'implementation_pk': 'implementation__id', }


class SolutionIISetField(InCasestudyField):
    """Returns a list of links to the solutions"""
    lookup_url_kwarg = 'solutioncategory_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'solutioncategory_pk': 'id', }


class SolutionInImplementationsListField(IdentityFieldMixin,
                                         SolutionInImplementationSetField):
    """Returns a Link to the solutions--list view"""
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id',
                            'implementation_pk': 'id', }


class StakeholderOfImplementaionField(InCaseStudyIdentityField):
    lookup_url_kwarg = 'pk'
    parent_lookup_kwargs = {
        'casestudy_pk': 'user__casestudy__id',
        'pk': 'coordinating_stakeholder__id',
        'stakeholdercategory_pk':
        'coordinating_stakeholder__stakeholder_category__id',}


class ImplementationSerializer(CreateWithUserInCasestudyMixin,
                               NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}
    solution_list = SolutionInImplementationsListField(
        source='solutioninimplementation_set',
        view_name='solutioninimplementation-list')
    sii_set = SolutionInImplementationSetField(
        source='solutioninimplementation_set',
        view_name='solutioninimplementation-detail',
        many=True,
        read_only=True)
    solution_set = SolutionIISetField(
        source='solutions',
        view_name='solution-detail',
        many=True)
    coordinating_stakeholder = StakeholderOfImplementaionField(
        view_name='stakeholder-detail')
    user = UserInCasestudyField(
        view_name='userincasestudy-detail')

    class Meta:
        model = Implementation
        fields = ('url', 'id', 'name', 'user',
                  'coordinating_stakeholder',
                  'solution_set',
                  'solution_list',
                  'sii_set',
                  )

    def update(self, obj, validated_data):
        """
        update the implementation-attributes,
        including selected solutions
        """
        implementation = obj
        implementation_id = implementation.id

        # handle solutions
        new_solutions = validated_data.pop('solutions', None)
        if new_solutions is not None:
            SolutionInImplementationModel = Implementation.solutions.through
            solution_qs = SolutionInImplementationModel.objects.filter(
                implementation=implementation)
            # delete existing solutions
            solution_qs.exclude(solution_id__in=(
                sol.id for sol in new_solutions)).delete()
            # add or update new solutions
            for sol in new_solutions:
                SolutionInImplementationModel.objects.update_or_create(
                    implementation=implementation,
                    solution=sol)

        # update other attributes
        obj.__dict__.update(**validated_data)
        obj.save()
        return obj


class ImplementationField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}


class SolutionInImplementationDetailListField(InCaseStudyIdentityField):
    lookup_url_kwarg = 'solution_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'implementation__user__casestudy__id',
                            'implementation_pk': 'implementation__id',
                            'solution_pk': 'id',
                            }


class SolutionInImplementationSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk':
                            'implementation__user__casestudy__id',
                            'implementation_pk': 'implementation__id',
                            }
    implementation = ImplementationField(
        view_name='implementation-detail')
    solution = SolutionField(view_name='solution-detail')
    solutioninimplementationnote_set = SolutionInImplementationDetailListField(
        view_name='solutioninimplementationnote-list')
    solutioninimplementationquantity_set = SolutionInImplementationDetailListField(
        view_name='solutioninimplementationquantity-list')
    solutioninimplementationgeometry_set = SolutionInImplementationDetailListField(
        view_name='solutioninimplementationgeometry-list')


    class Meta:
        model = SolutionInImplementation
        fields = ('url', 'id',
                  'implementation',
                  'solution',
                  'solutioninimplementationnote_set',
                  'solutioninimplementationquantity_set',
                  'solutioninimplementationgeometry_set',
                  )


class SolutionInImplementationField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'implementation__user__casestudy__id',
                            'implementation_pk': 'implementation__id',}


class SolutionInImplementationDetailCreateMixin:
    def create(self, validated_data):
        """Create a new solution quantity"""
        casestudy_pk = self.context['request'].session['casestudy_pk']
        sii = SolutionInImplementation.objects.get(id=casestudy_pk['solution_pk'])

        obj = self.Meta.model.objects.create(
            sii=sii,
            **validated_data)
        return obj


class SolutionInImplementationNoteSerializer(SolutionInImplementationDetailCreateMixin,
                                             NestedHyperlinkedModelSerializer):
    sii = SolutionInImplementationField(
        view_name='solutioninimplementation-detail',
        read_only=True)
    parent_lookup_kwargs = {
        'casestudy_pk': 'sii__implementation__user__casestudy__id',
        'implementation_pk': 'sii__implementation__id',
        'solution_pk': 'sii__id',
    }
    class Meta:
        model = SolutionInImplementationNote
        fields = ('url', 'id', 'note', 'sii')



class InSolutionField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk':
        'solution__solution_category__user__casestudy__id',
        'solutioncategory_pk': 'solution__solution_category__id',
        'solution_pk': 'solution__id',}
    extra_lookup_kwargs = {
        'solutioncategory_pk': 'sii__solution__solution_category__id',
        'solution_pk': 'sii__solution__id',}
    filter_field = 'solution_pk'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.casestudy_pk_lookup['solutioncategory_pk'] = \
            self.parent_lookup_kwargs['solutioncategory_pk']
        self.casestudy_pk_lookup['solution_pk'] = \
            self.parent_lookup_kwargs['solution_pk']


    """This is fixed in rest_framework_nested, but not yet available on pypi"""
    def use_pk_only_optimization(self):
        return False

    def get_queryset(self):
        """
        get the queryset limited to the current casestudy

        the casestudy might be on the objects instance,
        it might also be found in the session attribute "casestudy"

        Returns:
        --------
        queryset
        """
        view = self.root.context.get('view')
        Model = self.get_model(view)
        obj = self.root.instance
        kwargs = {}
        if obj:
            for pk, field_name in self.casestudy_pk_lookup.items():
                value = self.get_value_from_obj(obj, pk=pk)
                kwargs[field_name] = value
        else:
            casestudy_pk = view.request.session.get('casestudy_pk', {})
            value = casestudy_pk.get(self.filter_field)
            if value:
                Model = view.queryset.model
                kwargs2 = {self.root.parent_lookup_kwargs[self.filter_field]:
                           value}
                obj = Model.objects.filter(**kwargs2).first()

        if kwargs or kwargs2:
            return self.set_custom_query_params(obj, kwargs, Model)
        else:
            qs = view.queryset
        return qs

    def set_custom_query_params(self, obj, kwargs, Model):
        return  Model.objects.filter(**kwargs)

    def set_custom_query_params(self, obj, kwargs, Model):
        solution_id = obj.sii.solution.id
        qs = SolutionQuantity.objects.filter(solution__id=solution_id)
        return qs



    def get_value_from_obj(self, obj, pk='casestudy_pk'):
        casestudy_from_object = self.root.parent_lookup_kwargs.get(
            pk,
            self.extra_lookup_kwargs.get(pk))
        casestudy_pk = casestudy_from_object.split('__')
        for attr in casestudy_pk:
            obj = getattr(obj, attr)
        return obj

    def get_casestudy_pk(self):
        """
        get the casestudy primary key field from the casestudy_pk_lookup
        """
        casestudy_pk = self.casestudy_pk_lookup.get(
            'casestudy_pk',
            # or if not specified in the parent_lookup_kwargs
            self.parent_lookup_kwargs.get('casestudy_pk'))
        return casestudy_pk


class SolutionQuantityField(InSolutionField):
    parent_lookup_kwargs = {'casestudy_pk':
                            'solution__solution_category__user__casestudy__id',
                            'solutioncategory_pk': 'solution__solution_category__id',
                            'solution_pk': 'solution__id',}


class SolutionInImplementationQuantitySerializer(SolutionInImplementationNoteSerializer):
    quantity = SolutionQuantityField(view_name='solutionquantity-detail')
    class Meta:
        model = SolutionInImplementationQuantity
        fields = ('url', 'id', 'quantity', 'value', 'sii')


class SolutionInImplementationGeometrySerializer(SolutionInImplementationNoteSerializer):
    class Meta:
        model = SolutionInImplementationGeometry
        fields = ('url', 'id', 'name', 'geom', 'sii')

from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from repair.apps.login.models import CaseStudy, Profile, UserInCasestudy



class InCasestudyField(NestedHyperlinkedRelatedField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    child_lookup_kwargs = {'casestudy_pk': 'id'}

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
        if obj:
            casestudy_id = self.get_casestudyid_from_obj(obj)
        else:
            casestudy_id = view.request.session.get('casestudy')
        if casestudy_id:
            kwargs = {self.get_casestudy_pk(casestudy_id):
                      casestudy_id}
            qs = Model.objects.filter(**kwargs)
        else:
            qs = view.queryset
        return qs

    def get_model(self, view):
        Model = view.queryset.model
        RelatedModel = getattr(Model, self.field_name).field.related_model
        return RelatedModel

    def get_casestudyid_from_obj(self, obj):
        casestudy_pk = self.parent_lookup_kwargs['casestudy_pk'].split('__')
        for attr in casestudy_pk:
            obj = getattr(obj, attr)
        return obj

    def get_casestudy_pk(self, casestudy_id):
        casestudy_pk = self.child_lookup_kwargs.get('casestudy_pk')
        return casestudy_pk


class InCaseStudyIdentityField(InCasestudyField):
    """"""
    def __init__(self, view_name=None, **kwargs):
        assert view_name is not None, 'The `view_name` argument is required.'
        kwargs['read_only'] = True
        kwargs['source'] = '*'
        if 'lookup_url_kwarg' not in kwargs:
            kwargs['lookup_url_kwarg'] = self.lookup_url_kwarg
        super().__init__(view_name=view_name, **kwargs)

    def get_model(self, view):
        Model = view.queryset.model
        return Model


class UserSetField(InCaseStudyIdentityField):
    lookup_url_kwarg = 'casestudy_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'id'}


class SolutionCategorySetField(InCaseStudyIdentityField):
    lookup_url_kwarg = 'casestudy_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'id'}


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'id', 'name')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    groups = GroupSerializer(many=True)

    class Meta:
        model = User
        fields = ('url', 'id', 'username', 'email', 'groups', 'password')
        write_only_fields = ['password']
        read_only_fields = ['id', 'url']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        groups = validated_data.pop('groups', None)
        instance = User(**validated_data)
        instance.save()
        instance.groups = groups
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'password':
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance


class ProfileSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ('url', 'id', 'user', 'casestudies')


class CaseStudySerializer(serializers.HyperlinkedModelSerializer):
    userincasestudy_set = UserSetField(view_name='userincasestudy-list')
    stakeholder_categories = UserSetField(view_name='stakeholdercategory-list')
    solution_categories = UserSetField(view_name='solutioncategory-list')
    class Meta:
        model = CaseStudy
        fields = ('url', 'id', 'name', 'userincasestudy_set',
                  'solution_categories', 'stakeholder_categories')


class UserInCasestudySerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    class Meta:
        model = UserInCasestudy
        fields = ('url', 'id', 'user', 'name')
        read_only_fields = ['name']

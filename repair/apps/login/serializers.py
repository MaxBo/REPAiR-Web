from abc import ABC
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from rest_framework_nested.relations import NestedHyperlinkedRelatedField

from repair.apps.login.models import CaseStudy, Profile, UserInCasestudy


###############################################################################
#### Base Classes                                                          ####
###############################################################################

class IDRelatedField(serializers.PrimaryKeyRelatedField):
    """
    look for the related model of a related field
    and return all data from this model as a queryset
    """
    def get_queryset(self):
        view = self.root.context.get('view')
        Model = view.queryset.model
        # look up self.parent in the values of the dictionary self.root.fields
        # and return the key as the field_name
        field_name = self.get_field_name()
        # look recursively for related model
        for model_name in self.source_attrs[:-1]:
            Model = Model.profile.related.related_model
        RelatedModel = getattr(Model, field_name).field.related_model
        qs = RelatedModel.objects.all()
        return qs

    def get_field_name(self):
        field_name = {v: k for k, v in self.root.fields.items()}[self.parent]
        return field_name


class CreateWithUserInCasestudyMixin:
    """
    Abstrace Base Class for Creating an object
    with the UserInCasestudy defined if not given
    """
    def update(self, obj, validated_data):
        """
        update the implementation-attributes,
        including selected solutions
        """

        # update other attributes
        obj.__dict__.update(**validated_data)
        obj.save()
        return obj

    def create(self, validated_data):
        """Create a new user and its profile"""
        user = validated_data.pop('user', None)
        if not user:
            request = self.context['request']
            user_id = request.user.id or -1  # for the anonymus user
            casestudy_id = request.session.get('casestudy_pk', {}).\
                get('casestudy_pk')
            user = UserInCasestudy.objects.get(user_id=user_id,
                                               casestudy_id=casestudy_id)

        Model = self.get_model()
        obj = self.create_instance(Model, user, validated_data)
        self.update(obj=obj, validated_data=validated_data)
        return obj

    def create_instance(self, Model, user, validated_data):
        """Create the Instance"""
        required_fields = self.get_required_fields(user)
        for field in Model._meta.fields:
            if hasattr(field, 'blank') and field.blank == False:
                if field.name in validated_data:
                    required_fields[field.name] = validated_data.pop(field.name)
        obj = Model.objects.create(**required_fields)
        return obj

    def get_required_fields(self, user):
        required_fields = {}
        if 'user' in self.fields:
            required_fields['user'] = user
        return required_fields

    def get_model(self):
        view = self.root.context.get('view')
        Model = view.queryset.model
        return Model


class NestedHyperlinkedRelatedField2(NestedHyperlinkedRelatedField):
    def get_model(self, view):
        Model = view.queryset.model
        field_name = self.get_field_name()
        related_field = getattr(Model, field_name).field
        if related_field.model == Model:
            RelatedModel = related_field.related_model
        else:
            RelatedModel = related_field.model
        return RelatedModel

    def get_field_name(self):
        """get the field name from the serializer"""
        # build a dictionary if the fields (of the child_relations for fields
        # with many=True)
        if self.source and self.source != '*':
            return self.source
        fn_dict = {getattr(v, 'child_relation', v): k
                   for k, v in self.root.fields.items()}
        field_name = fn_dict.get(self, fn_dict.get(self))
        return field_name

    def get_object(self, view_name, view_args, view_kwargs):
        """
        Return the object corresponding to a matched URL.

        Takes the matched URL conf arguments, and should return an
        object instance, or raise an `ObjectDoesNotExist` exception.
        """

        # default lookup from rest_framework.relations.HyperlinkedRelatedField
        lookup_value = view_kwargs[self.lookup_url_kwarg]
        kwargs = {self.lookup_url_kwarg: lookup_value}

        # multi-level lookup
        for parent_lookup_kwarg, lookup_field in list(
            self.parent_lookup_kwargs.items()):
            lookup_value = view_kwargs[parent_lookup_kwarg]
            kwargs.update({lookup_field: lookup_value})

            return self.get_queryset().get(**kwargs)


class InCasestudyField(NestedHyperlinkedRelatedField2):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    filter_field = 'casestudy_pk'
    extra_lookup_kwargs = {}

    def __init__(self, *args, **kwargs):
        self.casestudy_pk_lookup = {
            'casestudy_pk': self.parent_lookup_kwargs['casestudy_pk']}

        super().__init__(*args, **kwargs)


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
            return self.set_custom_queryset(obj, kwargs, Model)
        else:
            casestudy_pk = view.request.session.get('casestudy_pk', {})
            value = casestudy_pk.get(self.filter_field)
            if value:
                RelatedModel = view.queryset.model
                kwargs2 = {self.root.parent_lookup_kwargs[self.filter_field]:
                           value}
                obj = RelatedModel.objects.filter(**kwargs2).first()
                return self.set_custom_queryset(obj, kwargs2, Model)
        qs = view.queryset
        return qs

    def set_custom_queryset(self, obj, kwargs, Model):
        """
        get objects from Model which meet the criteria
        defined in extra_lookup_kwargs
        (or if not defined in self.root.parent_lookup_kwargs)
        here, a value from `obj` is returned
        the field in Model is defined in self.parent_lookup_kwargs
        """
        pk = self.extra_lookup_kwargs.get(
            self.filter_field,
            self.root.parent_lookup_kwargs[self.filter_field])
        pk_attr = pk.split('__')
        if obj is None:
            kwargs = {}
        else:
            for attr in pk_attr:
                obj = getattr(obj, attr)
            kwargs = {self.parent_lookup_kwargs[self.filter_field]: obj,}
        qs = Model.objects.filter(**kwargs)
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

    #def set_custom_query_params(self, obj, kwargs, Model):
        #solution_pk_attr = self.extra_lookup_kwargs[self.filter_field].split('__')
        #for attr in solution_pk_attr:
            #obj = getattr(obj, attr)
        #kwargs = {self.parent_lookup_kwargs[self.filter_field]: obj,}
        #qs = Model.objects.filter(**kwargs)
        #return qs


class InUICField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'casestudy__id',
        'user_pk': 'user__id',}
    extra_lookup_kwargs = {}
    filter_field = 'user_pk'
    lookup_url_kwarg = 'user_pk'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.casestudy_pk_lookup['user_pk'] = \
            self.parent_lookup_kwargs['user_pk']


class IdentityFieldMixin:
    """Mixin to make a field that can be used with the ...-list view"""
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



class InCaseStudyIdentityField(IdentityFieldMixin, InCasestudyField):
    """
    A Field that returns only results for the casestudy
    that can be used with the ...-list view
    """


class InCasestudyListField(InCaseStudyIdentityField):
    """Field that returns a list of all items in the casestudy"""
    lookup_url_kwarg = 'casestudy_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'id'}


class InUICSetField(IdentityFieldMixin, InUICField):
    """Field that returns a list of all items of the user in the casestudy"""


###############################################################################
#### Serializers for the Whole Project                                     ####
###############################################################################

class GroupSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    class Meta:
        model = Group
        fields = ('url', 'id', 'name')


class UserSerializer(NestedHyperlinkedModelSerializer):
    """Serializer for put and post requests"""
    parent_lookup_kwargs = {}
    casestudies = serializers.HyperlinkedRelatedField(
        queryset = CaseStudy.objects.all(),
        source='profile.casestudies',
        many=True,
        view_name='casestudy-detail',
        help_text=_('Select the Casestudies the user works on')
    )
    organization = serializers.CharField(source='profile.organization',
                                         allow_blank=True, required=False)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        organization = serializers.CharField(required=False, allow_null=True)
        fields = ('url', 'id', 'username', 'email', 'groups', 'password',
                  'organization', 'casestudies',
                  )

    def update(self, obj, validated_data):
        """update the user-attributes, including profile information"""
        user = obj
        user_id = user.id

        # handle groups
        new_groups = validated_data.pop('groups', None)
        if new_groups is not None:
            UserInGroups = User.groups.through
            group_qs = UserInGroups.objects.filter(user=user)
            # delete existing groups
            group_qs.exclude(group_id__in=(gr.id for gr in new_groups)).delete()
            # add or update new groups
            for gr in new_groups:
                UserInGroups.objects.update_or_create(user=user,
                                                      group=gr)

        # handle profile
        profile_data = validated_data.pop('profile', None)
        if profile_data is not None:
            profile = Profile.objects.get(id=user_id)
            new_casestudies = profile_data.pop('casestudies', None)
            if new_casestudies is not None:
                casestudy_qs = UserInCasestudy.objects.filter(user=user_id)
                # delete existing
                casestudy_qs.exclude(id__in=(cs.id for cs in new_casestudies))\
                    .delete()
                # add or update new casestudies
                for cs in new_casestudies:
                    UserInCasestudy.objects.update_or_create(user=profile,
                                                             casestudy=cs)

            # update other profile attributes
            profile.__dict__.update(**profile_data)
            profile.save()

        # update other attributes
        obj.__dict__.update(**validated_data)
        obj.save()
        return obj

    def create(self, validated_data):
        """Create a new user and its profile"""
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        user = User.objects.create_user(username, email, password)
        self.update(obj=user, validated_data=validated_data)
        return user


class CaseStudySerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    userincasestudy_set = InCasestudyListField(view_name='userincasestudy-list')
    stakeholder_categories = InCasestudyListField(
        view_name='stakeholdercategory-list')
    solution_categories = InCasestudyListField(
        view_name='solutioncategory-list')
    implementations = InCasestudyListField(view_name='implementation-list')
    materials = InCasestudyListField(view_name='materialincasestudy-list')
    activitygroups = InCasestudyListField(view_name='activitygroup-list')

    class Meta:
        model = CaseStudy
        fields = ('url', 'id', 'name', 'userincasestudy_set',
                  'solution_categories', 'stakeholder_categories',
                  'implementations',
                  'materials',
                  'activitygroups',
                  )


class UserInCasestudyField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    extra_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}


class UserInCasestudySerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    role = serializers.CharField(required=False, allow_blank=True)
    user = serializers.HyperlinkedIdentityField(
        source='user.user',
        view_name='user-detail',
    )
    implementations = InUICSetField(view_name='implementation-list')

    class Meta:
        model = UserInCasestudy
        fields = ('url', 'id', 'user', 'name', 'role', 'implementations')
        read_only_fields = ['name']



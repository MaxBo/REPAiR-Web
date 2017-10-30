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
            casestudy_id = request.session.get('casestudy')
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
        required_fields = {'user': user,}
        return required_fields

    def get_model(self):
        view = self.root.context.get('view')
        Model = view.queryset.model
        return Model


class InCasestudyField(NestedHyperlinkedRelatedField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    child_lookup_kwargs = {'casestudy_pk': 'id'}

    def __init__(self, *args, **kwargs):
        self.child_lookup_kwargs = kwargs.pop('child_lookup_kwargs', None) \
            or self.child_lookup_kwargs
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
        RelatedModel = getattr(Model, self.get_field_name()).field.related_model
        return RelatedModel

    def get_field_name(self):
        fn_dict = {v: k for k, v in self.root.fields.items()}
        field_name = fn_dict.get(self, fn_dict.get(self.parent))
        return field_name

    def get_casestudyid_from_obj(self, obj):
        child_lookup_kwargs = self._kwargs.get('child_lookup_kwargs',
                                               self.child_lookup_kwargs)
        casestudy_pk = child_lookup_kwargs['casestudy_pk'].split('__')
        for attr in casestudy_pk:
            obj = getattr(obj, attr)
        return obj

    def get_casestudy_pk(self, casestudy_id):
        casestudy_pk = self.parent_lookup_kwargs.get('casestudy_pk')
        return casestudy_pk

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


class InCasestudySetField(InCaseStudyIdentityField):
    """Field that returns a list of all items in the casestudy"""
    lookup_url_kwarg = 'casestudy_pk'
    parent_lookup_kwargs = {'casestudy_pk': 'id'}

###############################################################################
#### Serializers for the Whole Project                                     ####
###############################################################################

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'id', 'name')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """Serializer for put and post requests"""
    casestudies = serializers.HyperlinkedRelatedField(
        queryset = CaseStudy.objects.all(),
        source='profile.casestudies',
        many=True,
        view_name='casestudy-detail',
        help_text=_('Select the Casestudies the user works on')
    )
    organization = serializers.CharField(source='profile.organization')

    class Meta:
        model = User
        fields = ('url', 'id', 'username', 'email', 'groups', 'password',
                  'organization', 'casestudies')
        write_only_fields = ['password']
        read_only_fields = ['id', 'url']

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


class CaseStudySerializer(serializers.HyperlinkedModelSerializer):
    userincasestudy_set = InCasestudySetField(view_name='userincasestudy-list')
    stakeholder_categories = InCasestudySetField(
        view_name='stakeholdercategory-list')
    solution_categories = InCasestudySetField(
        view_name='solutioncategory-list')
    implementations = InCasestudySetField(view_name='implementation-list')

    class Meta:
        model = CaseStudy
        fields = ('url', 'id', 'name', 'userincasestudy_set',
                  'solution_categories', 'stakeholder_categories',
                  'implementations')


class UserInCasestudySerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    user = serializers.HyperlinkedIdentityField(
        source='user.user',
        view_name='user-detail',
    )
    class Meta:
        model = UserInCasestudy
        fields = ('url', 'id', 'user', 'name', 'role')
        read_only_fields = ['name']


class UserInCasestudyField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}

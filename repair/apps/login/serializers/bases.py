
from django.contrib.gis import geos
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import serializers
from rest_framework.exceptions import (
    PermissionDenied, ValidationError as DRFValidationError)
from rest_framework_nested.relations import NestedHyperlinkedRelatedField
from rest_framework.utils import model_meta
from django.http import HttpResponseBadRequest

from repair.apps.login.models import CaseStudy, Profile, UserInCasestudy
from repair.apps.asmfa.models import KeyflowInCasestudy

###############################################################################
#### Base Classes                                                          ####
###############################################################################

class DynamicFieldsModelSerializerMixin:
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        fields = self.context['request'].query_params.get('fields')
        if fields:
            fields = fields.split(',')
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


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
        field_name = self.source or self.get_field_name()
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

    def update(self, instance, validated_data):
        """
        update the implementation-attributes,
        including selected solutions
        """
        info = model_meta.get_field_info(instance.__class__)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in validated_data):
                many_to_many[field_name] = validated_data.pop(field_name)

        # update other attributes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Save many-to-many relationships after the instance is created.
        if many_to_many:
            for field_name, value in many_to_many.items():
                field = getattr(instance, field_name)
                field.set(value)

        return instance

    def create(self, validated_data):
        """Create a new user and its profile"""
        user = validated_data.pop('user', None)
        if not user:
            request = self.context['request']
            # create as anonymus user if not user provided
            user_id = -1 if request.user.id is None else request.user.id
            url_pks = request.session.get('url_pks', {})
            casestudy_id = url_pks.get('casestudy_pk')
            try:
                user = UserInCasestudy.objects.get(user_id=user_id,
                                                   casestudy_id=casestudy_id)
            except (ObjectDoesNotExist, TypeError, ValueError):
                user = Profile.objects.get(id=user_id)
                casestudy = CaseStudy.objects.get(id=casestudy_id)
                msg = _('User {} has no permission to access casestudy {}'
                        .format(user, casestudy))
                raise PermissionDenied(detail=msg)

        # get the keyfloy in casestudy if exists
        request = self.context['request']
        url_pks = request.session.get('url_pks', {})
        keyflow_id = url_pks.get('keyflow_pk')
        keyflow_in_casestudy = None
        if keyflow_id is not None:
            try:
                keyflow_in_casestudy = KeyflowInCasestudy.objects.get(
                    pk=keyflow_id)
            except (ObjectDoesNotExist, TypeError, ValueError):
                pass

        Model = self.get_model()
        instance = self.create_instance(Model, user, validated_data,
                                        kic=keyflow_in_casestudy)
        self.update(instance=instance, validated_data=validated_data)
        return instance

    def create_instance(self, Model, user, validated_data, kic=None):
        """Create the Instance"""
        required_fields = self.get_required_fields(user, kic)
        for field in Model._meta.fields:
            if hasattr(field, 'blank') and not field.blank:
                if field.name in validated_data:
                    required_fields[field.name] = validated_data.pop(field.name)
                elif field.name + '_id' in validated_data:
                    required_fields[field.name + '_id'] = \
                        validated_data.pop(field.name + '_id')
        try:
            obj = Model.objects.create(**required_fields)
        except ValidationError as e:
            raise DRFValidationError(detail=str(e))
        return obj

    def get_required_fields(self, user, kic):
        required_fields = {}
        if 'user' in self.fields:
            required_fields['user'] = user
        if kic:
            if 'keyflow' in self.fields:
                required_fields['keyflow'] = kic
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


class InCasestudySerializerMixin:
    """get casestudy from session.url_pks and use this in update and create"""
    def get_casestudy(self):
        url_pks = self.context['request'].session['url_pks']
        casestudy_pk = url_pks['casestudy_pk']
        casestudy = CaseStudy.objects.get(id=casestudy_pk)
        return casestudy

    def create(self, validated_data):
        """Create a new keyflow in casestury"""
        casestudy = self.get_casestudy()
        obj = self.Meta.model.objects.create(
            casestudy=casestudy,
            **validated_data)
        return obj

    def update(self, instance, validated_data):
        casestudy = self.get_casestudy()
        validated_data['casestudy'] = casestudy
        return super().update(instance, validated_data)


class InCasestudyField(NestedHyperlinkedRelatedField2):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    filter_field = 'casestudy_pk'
    extra_lookup_kwargs = {}

    def __init__(self, *args, **kwargs):
        self.url_pks_lookup = {
            'casestudy_pk': self.parent_lookup_kwargs['casestudy_pk']}

        super().__init__(*args, **kwargs)

    def use_pk_only_optimization(self):
        """This is fixed in rest_framework_nested, but not yet available on pypi"""
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
            for pk, field_name in self.url_pks_lookup.items():
                value = self.get_value_from_obj(obj, pk=pk)
                kwargs[field_name] = value
            return self.set_custom_queryset(obj, kwargs, Model)
        else:
            url_pks = view.request.session.get('url_pks', {})
            value = url_pks.get(self.filter_field)
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
            kwargs = {self.parent_lookup_kwargs[self.filter_field]: obj, }
        qs = Model.objects.filter(**kwargs)
        return qs

    def get_value_from_obj(self, obj, pk='casestudy_pk'):
        """
        get the value of the field defined by `pk` from the obj

        Parameters
        ----------
        obj: django-object
            the object
        pk: str
          the key
        """
        pk_field_from_object = self.root.parent_lookup_kwargs.get(
            pk,
            self.extra_lookup_kwargs.get(pk))
        url_pk = pk_field_from_object.split('__')
        value = obj
        for attr in url_pk:
            value = getattr(value, attr)
        return value

    def get_casestudy_pk(self):
        """
        get the casestudy primary key field from the url_pks_lookup
        """
        casestudy_pk = self.url_pks_lookup.get(
            'casestudy_pk',
            # or if not specified in the parent_lookup_kwargs
            self.parent_lookup_kwargs.get('casestudy_pk'))
        return casestudy_pk


class InSolutionField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk':
        'solution__solution_category__keyflow__id',
        'solutioncategory_pk': 'solution__solution_category__id',
        'solution_pk': 'solution__id', }
    extra_lookup_kwargs = {
        'solutioncategory_pk': 'sii__solution__solution_category__id',
        'solution_pk': 'sii__solution__id', }
    filter_field = 'solution_pk'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url_pks_lookup['solutioncategory_pk'] = \
            self.parent_lookup_kwargs['solutioncategory_pk']
        self.url_pks_lookup['solution_pk'] = \
            self.parent_lookup_kwargs['solution_pk']


class InUICField(InCasestudyField):
    parent_lookup_kwargs = {
        'casestudy_pk': 'casestudy__id',
        'user_pk': 'user__id', }
    extra_lookup_kwargs = {}
    filter_field = 'user_pk'
    lookup_url_kwarg = 'user_pk'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url_pks_lookup['user_pk'] = \
            self.parent_lookup_kwargs['user_pk']


class ForceMultiMixin:
    """Convert Polygon to Multipolygon, if required"""
    @staticmethod
    def convert2multi(validated_data, geo_field):
        geom = validated_data.get(geo_field, None)
        if geom and isinstance(geom, geos.Polygon):
            geom = geos.MultiPolygon(geom)
            validated_data[geo_field] = geom


class IdentityFieldMixin:
    """Mixin to make a field that can be used with the ...-list view"""
    def __init__(self, view_name=None, **kwargs):
        assert view_name is not None, 'The `view_name` argument is required.'
        kwargs['read_only'] = True
        kwargs['source'] = '*'
        if 'lookup_url_kwarg' not in kwargs:
            kwargs['lookup_url_kwarg'] = self.lookup_url_kwarg
        super().__init__(view_name=view_name, **kwargs)

    @staticmethod
    def get_model(view):
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

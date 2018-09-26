
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework_nested.serializers import NestedHyperlinkedModelSerializer
from rest_framework_nested.relations import NestedHyperlinkedRelatedField
from rest_framework_gis.serializers import (GeoFeatureModelSerializer,
                                            GeoFeatureModelListSerializer,
                                            GeometryField)
from publications_bootstrap.models import Publication

from repair.apps.login.models import CaseStudy, Profile, UserInCasestudy

from .bases import (ForceMultiMixin,
                    InCasestudyField,
                    InCasestudyListField,
                    InUICSetField,
                    IDRelatedField)

###############################################################################
#### Serializers for the login app                                         ####
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
        queryset = CaseStudy.objects,
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

    def update(self, instance, validated_data):
        """update the user-attributes, including profile information"""
        user = instance
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
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            #profile.__dict__.update(**profile_data)
            profile.save()

        # update other attributes
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if 'password' in validated_data:
            instance.set_password(validated_data['password'])

        instance.save()
        return instance

    def create(self, validated_data):
        """Create a new user and its profile"""
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        user = User.objects.create_user(username, email, password)
        self.update(instance=user, validated_data=validated_data)
        return user


class CaseStudySerializer(ForceMultiMixin,
                          GeoFeatureModelSerializer,
                          NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    userincasestudy_set = InCasestudyListField(
        view_name='userincasestudy-list')
    stakeholder_categories = InCasestudyListField(
        view_name='stakeholdercategory-list')
    keyflows = InCasestudyListField(view_name='keyflowincasestudy-list')
    levels = InCasestudyListField(view_name='adminlevels-list')
    publications = InCasestudyListField(source='publicationincasestury_set',
        view_name='publicationincasestudy-list')
    aims = InCasestudyListField(view_name='aim-list')
    challenges = InCasestudyListField(view_name='challenge-list')
    #default_area_level = IDRelatedField(required=False, allow_null=True)
    show_on_welcome_map = serializers.BooleanField(required=False)

    class Meta:
        model = CaseStudy
        geo_field = 'geom'
        fields = ('url', 'id', 'name', 'userincasestudy_set',
                  'stakeholder_categories',
                  'keyflows',
                  'levels',
                  'focusarea',
                  'publications',
                  'aims',
                  'challenges',
                  'description',
                  #'default_area_level',
                  'show_on_welcome_map'
                  )

    def update(self, instance, validated_data):
        """cast geomfield to multipolygon"""
        geo_field = self.Meta.geo_field
        self.convert2multi(validated_data, geo_field)
        self.convert2multi(validated_data, 'focusarea')
        return super().update(instance, validated_data)


class CaseStudyListSerializer(GeoFeatureModelListSerializer,
                              CaseStudySerializer):
    """Coasestudies as FeatureCollection"""


class CasestudyField(NestedHyperlinkedRelatedField):
    parent_lookup_kwargs = {'pk': 'id'}
    queryset = CaseStudy.objects
    """This is fixed in rest_framework_nested, but not yet available on pypi"""
    def use_pk_only_optimization(self):
        return False


class UserInCasestudyField(InCasestudyField):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    extra_lookup_kwargs = {'casestudy_pk': 'user__casestudy__id'}


class UserInCasestudySerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    role = serializers.CharField(required=False, allow_blank=True)
    user = IDRelatedField()

    class Meta:
        model = UserInCasestudy
        fields = ('url', 'id', 'user', 'name', 'role')
        read_only_fields = ['name']


class PublicationSerializer(NestedHyperlinkedModelSerializer):
    parent_lookup_kwargs = {}
    class Meta:
        model = Publication
        fields = ('id', 'title', 'authors', 'doi', 'url')

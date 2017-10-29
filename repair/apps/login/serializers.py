from django.contrib.auth.models import User, Group
from django.forms.models import model_to_dict
from repair.apps.login.models import CaseStudy, Profile, UserInCasestudy
from rest_framework import serializers


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
    class Meta:
        model = CaseStudy
        fields = ('url', 'id', 'name')


class UserInCasestudySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserInCasestudy
        fields = ('url', 'id', 'user', 'casestudy')

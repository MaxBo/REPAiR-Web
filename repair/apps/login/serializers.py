from django.contrib.auth.models import User, Group
from repair.apps.login.models import CaseStudy, GDSEUser
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')

class GDSEUserSerializer(serializers.HyperlinkedModelSerializer):
    user = UserSerializer
    class Meta:
        model = GDSEUser
        fields = ('id', 'user', 'casestudies')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')


class CaseStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStudy
        fields = ('id', 'name')

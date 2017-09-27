from repair.apps.study_area.models import Links, Nodes
from django.contrib.auth.models import User, Group
from rest_framework import serializers

class LinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Links
        fields = ('id_from', 'id_to', 'weight')

class NodesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nodes
        fields = ('location', 'x_coord', 'y_coord')
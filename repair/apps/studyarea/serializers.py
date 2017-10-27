from repair.apps.studyarea.models import (StakeholderCategory,
                                          Stakeholder,
                                          )

from rest_framework import serializers


class StakeholderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stakeholder
        fields = ('id', 'name')


class StakeholderCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = StakeholderCategory
        fields = ('id', 'name')

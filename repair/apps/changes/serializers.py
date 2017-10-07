from repair.apps.changes.models import (CaseStudy,
                                        Unit,
                                        User,
                                        StakeholderCategory,
                                        Stakeholder,
                                        SolutionCategory,
                                        Solution)

from rest_framework import serializers


class CaseStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStudy
        fields = ('id', 'name')


class StakeholderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stakeholder
        fields = ('id', 'name')


class StakeholderCategorySerializer(serializers.ModelSerializer):
    stakeholders = StakeholderSerializer(many=True, read_only=True)

    class Meta:
        model = StakeholderCategory
        fields = ('id', 'name', 'stakeholders')

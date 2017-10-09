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

    class Meta:
        model = StakeholderCategory
        fields = ('id', 'name')


class SolutionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Solution
        fields = ('id', 'name', 'user', 'description')


class SolutionCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SolutionCategory
        fields = ('id', 'name')

from repair.apps.changes.models import (Unit,
                                        SolutionCategory,
                                        Solution)

from rest_framework import serializers




class SolutionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Solution
        fields = ('id', 'name', 'user', 'description', 'one_unit_equals')


class SolutionPostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Solution
        fields = ('id', 'name', 'user', 'description', 'one_unit_equals',
                  'solution_category')


class SolutionCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SolutionCategory
        fields = ('id', 'name')


class SolutionCategoryPostSerializer(serializers.ModelSerializer):

    class Meta:
        model = SolutionCategory
        fields = ('id', 'name', 'user')


from repair.apps.changes.models import (CaseStudy,
                                          Unit,
                                          UserAP12,
                                          UserAP34,
                                          StakeholderCategory,
                                          Stakeholder,
                                          SolutionCategory,
                                          Solution)

from rest_framework import serializers

class CaseStudySerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStudy
        fields = ('id', 'name')


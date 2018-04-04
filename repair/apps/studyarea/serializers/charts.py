from rest_framework.serializers import ModelSerializer

from repair.apps.studyarea.models import ChartCategory, Chart
from repair.apps.login.serializers import IDRelatedField


class ChartCategorySerializer(ModelSerializer):
    parent_lookup_kwargs = {'casestudy_pk': 'casestudy__id'}
    class Meta:
        model = ChartCategory
        fields = ('id', 'name')


class ChartSerializer(ModelSerializer):
    parent_lookup_kwargs = {
        'casestudy_pk': 'chart_category__casestudy__id', 
        'chartcategory_pk': 'chart_category__id',
    }
    chart_category = IDRelatedField(read_only=True)
    
    class Meta:
        model = Chart
        fields = ('id', 'name', 'image', 'chart_category')
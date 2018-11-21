from repair.apps.utils.serializers import (BulkSerializerMixin,
                                           Reference)
from repair.apps.studyarea.serializers.areas import (AdminLevelSerializer,
                                                     AreaSerializer)
from repair.apps.studyarea.models import (AdminLevels, Area)
from django.db import transaction


class AdminLevelCreateSerializer(BulkSerializerMixin, AdminLevelSerializer):
    field_map = {
        'name': 'name',
        'level': 'level'
    }
    index_columns = ['level', 'name']

    def get_queryset(self):
        return AdminLevels.objects.filter(casestudy=self.casestudy)

    def save_data(self, dataframe):
        #  delete old models, there are unique constraint on (casestudy, level)
        # AND (casestudy, name) interferring with each other otherwise
        qs = self.get_queryset()
        with transaction.atomic():
            qs.delete()
            res = super().save_data(dataframe)
        return res


class AreaCreateSerializer(BulkSerializerMixin, AdminLevelSerializer):
    field_map = {
        'parent': Reference(name='parent_area',
                            referenced_field='name',
                            referenced_model=Area,
                            allow_null=True),
        'adminlevel': 'adminlevel',
        'name': 'name',
        'code': 'code',
        'wkt': 'geom'
    }
    index_columns = ['code']

    def get_queryset(self):
        return Area.objects.filter(casestudy=self.casestudy)



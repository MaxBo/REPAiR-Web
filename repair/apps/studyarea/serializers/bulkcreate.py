from repair.apps.utils.serializers import (BulkSerializerMixin,
                                           Reference)
from repair.apps.studyarea.serializers.areas import (AdminLevelSerializer,
                                                     AreaSerializer)
from repair.apps.studyarea.models import (AdminLevels, Area)
from django.db import transaction


class CasestudyUpdateSerializer(BulkSerializerMixin, AdminLevelSerializer):
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


class AreaCreateSerializer(BulkSerializerMixin, AreaSerializer):
    field_map = {
        'parent': Reference(name='parent_area',
                            referenced_field='code',
                            referenced_model=Area,
                            allow_null=True,
                            filter_args={
                                'adminlevel__casestudy': '@casestudy',
                            }),
        'adminlevel': Reference(name='adminlevel',
                                referenced_field='level',
                                referenced_model=AdminLevels,
                                allow_null=True),
        'name': 'name',
        'code': 'code',
        'wkt': 'geom'
    }
    index_columns = ['code']

    def get_queryset(self):
        return Area.objects.filter(adminlevel__casestudy=self.casestudy)


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

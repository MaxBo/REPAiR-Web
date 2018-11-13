import pandas as pd
import numpy as np
import tempfile
from django_pandas.io import read_frame
from django.utils.translation import ugettext as _
from repair.apps.utils.serializers import (BulkSerializerMixin,
                                           MalformedFileError,
                                           ForeignKeyNotFound,
                                           ValidationError,
                                           TemporaryMediaFile,
                                           BulkResult,
                                           Reference)
from repair.apps.asmfa.serializers import (ActivityGroupSerializer,
                                           ActivitySerializer,
                                           ActorSerializer
                                           )
from repair.apps.asmfa.models import (KeyflowInCasestudy,
                                      ActivityGroup,
                                      Activity,
                                      Actor
                                      )


class ActivityGroupCreateSerializer(BulkSerializerMixin,
                                    ActivityGroupSerializer):

    field_map = {
        'code': 'code',
        'name': 'name'
    }
    index_column = 'code'

    def get_queryset(self):
        return ActivityGroup.objects.filter(keyflow=self.keyflow)


class ActivityCreateSerializer(BulkSerializerMixin,
                               ActivitySerializer):

    field_map = {
        'nace': 'nace',
        'name': 'name',
        'ag': Reference(name='activitygroup',
                        referenced_field='code',
                        referenced_model=ActivityGroup,
                        filter_args={'keyflow': '@keyflow'}),
    }
    index_column = 'nace'

    def get_queryset(self):
        return Activity.objects.filter(activitygroup__keyflow=self.keyflow)


class ActorCreateSerializer(BulkSerializerMixin,
                            ActorSerializer):

    field_map = {
        'BvD ID number': 'BvDid',
        'Company name': 'name',
        'Cons.code': 'consCode',
        'Lastavail.year': 'year',
        'Trade description (English)': 'description_eng',
        'Trade description in original language': 'description',
        'BvD Independence Indicator': 'BvDii',
        'Website address': 'website',
        'Number of employeesLast avail. yr': 'employees',
        'Operating revenue (Turnover) (last value)th EUR': 'turnover',
        'NACE Rev. 2Core code (4 digits)': Reference(
            name='activity',
            referenced_field='nace',
            referenced_model=Activity,
            filter_args={'activitygroup__keyflow': '@keyflow'}
        )
    }
    index_column = 'BvD ID number'

    def get_queryset(self):
        return Actor.objects.filter(
            activity__activitygroup__keyflow=self.keyflow)

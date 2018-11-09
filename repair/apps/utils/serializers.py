from typing import Type
import pandas as pd
from django_pandas.io import read_frame
import numpy as np
import os
from django.utils.translation import ugettext as _
from tempfile import NamedTemporaryFile
from rest_framework import serializers
from django.db.models import Model
from django.db.models.query import QuerySet
from django.conf import settings

from repair.apps.asmfa.models import KeyflowInCasestudy


class BulkValidationError(Exception):
    def __init__(self, message, path=''):
        super().__init__(message)
        self.message = message
        self.path = path


class FileFormatError(BulkValidationError):
    """File Encoding is broken"""


class MalformedFileError(BulkValidationError):
    """the file content is malformed (e.g. missing columns)"""


class ValidationError(BulkValidationError):
    """general error occurring while validating data"""


class ForeignKeyNotFound(BulkValidationError):
    """related foreign key in file content not found in existing data"""


class BulkResult:
    def __init__(self, queryset, rows_added=0, rows_updated=0):
        self.rows_added = rows_added
        self.rows_updated = rows_updated
        self.queryset = queryset


def TemporaryMediaFile():
    '''
    temporary file served in the media folder,
    file.url - relative url to access file
    file.name - path to file
    '''
    path = os.path.join(settings.MEDIA_ROOT, 'tmp')
    if not os.path.exists(path):
        os.mkdir(path)
    wrapper = NamedTemporaryFile(mode='w', dir=path, delete=False)
    p, fn = os.path.split(wrapper.name)
    wrapper.file.url = os.path.join(settings.MEDIA_URL, fn)
    return wrapper


class Reference:
    """
    merge models from queryset to data by foreign key

    Parameters
    ----------
    referenced_model: Model
        queryset of the referenced Modelreferencing_column
    referenced_field: str
        the field referenced in the model
    filter_args: str, optional(default: all models)
        filter-expressions to filter the models by, values may also start with
        '@' followed by a name, those name can be related to attributes of a
        given object when calling merge() later
    name: str, optional(default: referencing column passed to merge())
        the name of the column in the dataset where the referenced models will
        be put into, created when not existing
    """
    def __init__(self, name: str, referenced_field: str,
                 referenced_model: Type[Model], filter_args: dict={}):
        self.name = name
        self.referenced_column = referenced_field
        self.referenced_model = referenced_model
        self.filter_args = filter_args


    def merge(self, data: pd.DataFrame, referencing_column: str,
              rel: object=None):
        """
        merges the referenced models to the given data

        Parameters
        ----------
        data: pd.Dataframe
            the dataframe with the rows to check
        rel: if @ was defined in filter_args, the object is related to
        referencing_column: str
            the referencing column in data that should be checked


        Returns
        -------
        existing_keys: pd.Dataframe
            the merged dataframe
        missing_rows: pd.Dataframe
            the rows in the df_new where rows are missing
        """
        objects = self.referenced_model.objects
        if self.filter_args:
            for k, v in self.filter_args.items():
                if v.startswith('@'):
                    if not rel:
                        raise Exception('You defined a related keyword in the '
                                        'filter_args but did not pass the related '
                                        'object')
                    self.filter_args[k] = getattr(rel, v[1:])
            referenced_queryset = objects.filter(**self.filter_args)
        else:
            referenced_queryset = objects.all()
        # only the id of the referenced queryset is relevant
        fieldnames = ['id', self.referenced_column]
        # get existing rows in the referenced table of the keyflow
        df_referenced = read_frame(referenced_queryset,
                                   index_col=[self.referenced_column],
                                   fieldnames=fieldnames)
        df_referenced['_models'] = referenced_queryset

        # check if an activitygroup exist for each activity
        df_merged = data.merge(df_referenced,
                               left_on=referencing_column,
                               right_index=True,
                               how='left',
                               indicator=True,
                               suffixes=['', '_old'])

        missing_rows = df_merged.loc[df_merged._merge=='left_only']
        existing_rows = df_merged.loc[df_merged._merge=='both']

        if self.name:
            existing_rows[self.name] = existing_rows['_models']
        else:
            existing_rows[referencing_column] = existing_rows['_models']

        tmp_columns = ['_merge', 'id', '_models']

        missing_rows.drop(columns=tmp_columns, inplace=True)
        existing_rows.drop(columns=tmp_columns, inplace=True)
        return existing_rows, missing_rows


class BulkSerializerMixin(metaclass=serializers.SerializerMetaclass):
    bulk_upload = serializers.FileField(required=False,
                                        write_only=True)
    # important: input file will be checked if it contains those columns
    # (letter case doesn't matter)
    field_map = {}

    def __init_subclass__(cls, **kwargs):
        """add bulk_upload to the cls.Meta if it does not exist there"""
        fields = cls.Meta.fields
        if fields and 'bulk_upload' not in fields:
            cls.Meta.fields = fields + ('bulk_upload', )
        return super().__init_subclass__(**kwargs)

    @property
    def keyflow(self):
        request = self.context['request']
        url_pks = request.session.get('url_pks', {})
        keyflow_id = url_pks.get('keyflow_pk')
        if not keyflow_id:
            return None
        return KeyflowInCasestudy.objects.get(id=keyflow_id)


    def to_internal_value(self, data):
        """
        Convert csv-data to pandas dataframe and
        add it as attribute `dataframe` to the validated data
        add also `keyflow_id` to validated data
        """
        file = data.pop('bulk_upload', None)
        if file is None:
            return super().to_internal_value(data)

        # other fields are not required when bulk uploading
        fields = self._writable_fields
        for field in fields:
            field.required = False
        ret = super().to_internal_value(data)  # would throw exc. else

        encoding = 'cp1252'
        try:
            df_new = pd.read_csv(file[0], sep='\t', encoding=encoding)
        except pd.errors.ParserError as e:
            raise MalformedFileError(str(e))

        df_new = df_new.\
            rename(columns={c: c.lower() for c in df_new.columns})

        df_mapped = self.map_fields(df_new)
        ret['dataframe'] = df_mapped

        return ret

    def map_fields(self, data):

        bulk_columns = [c.lower() for c in self.field_map.keys()]
        missing_cols = list(set(bulk_columns).difference(set(data.columns)))

        if missing_cols:
            raise MalformedFileError(
                _('The following columns are missing: {}'.format(missing_cols)))

        for column, field in self.field_map.items():
            if isinstance(field, Reference):
                data, missing = field.merge(
                    data, referencing_column=column, rel=self)

                if len(missing) > 0:
                    missing_values = np.unique(missing['column'].values)
                    with TemporaryMediaFile() as f:
                        # ToDo: create a file highlighting the errors in the input data
                        # will be returned as an error response
                        df_act_new.to_csv(f, sep='\t')
                    raise ForeignKeyNotFound(
                        _('Related models {} not found'
                          .format(missing_values)),
                        f.url
                    )
            else:
                data = data.rename(columns={column: field})

        return data


    def create(self, validated_data):
        if 'dataframe' not in validated_data:
            return super().create(validated_data)
        return self.bulk_create(validated_data)

    def bulk_create(self, validated_data):
        '''
        bulk create models based on 'dataframe' in validated_data

        Returns
        ----------------
        BulkResult
        '''
        raise NotImplementedError('`bulk_create()` must be implemented.')

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        if isinstance(instance, BulkResult):
            ret = {
                'count': len(instance.queryset),
                'added': instance.rows_added,
                'updated': instance.rows_updated
            }
            results = ret['results'] = []
            for model in instance.queryset:
                results.append(super().to_representation(model))
            return ret
        return super().to_representation(instance)


class EnumField(serializers.ChoiceField):
    def __init__(self, enum, **kwargs):
        self.enum = enum
        kwargs['choices'] = [(e.name, e.name) for e in enum]
        super(EnumField, self).__init__(**kwargs)

    def to_representation(self, obj):
        return obj.name

    def to_internal_value(self, data):
        try:
            if data not in self.enum._member_names_:
                data = data.upper()
            return self.enum[data]
        except KeyError:
            self.fail('invalid_choice', input=data)

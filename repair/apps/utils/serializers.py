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
from copy import deepcopy

from repair.apps.asmfa.models import KeyflowInCasestudy
from repair.apps.login.models import CaseStudy


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
    def __init__(self, created=[], updated=[], message=''):
        self.created = created
        self.updated = updated
        self.message = message


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
    wrapper.file.url = settings.MEDIA_URL + '/tmp/' + fn
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
        self.filter_args = filter_args.copy()


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
            filter_args = self.filter_args.copy()
            for k, v in filter_args.items():
                if v.startswith('@'):
                    if not rel:
                        raise Exception('You defined a related keyword in the '
                                        'filter_args but did not pass the '
                                        'related object')
                    filter_args[k] = getattr(rel, v[1:])
            referenced_queryset = objects.filter(**filter_args)
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

    # column, if remapped put the name of the field here
    index_column = None

    def __init_subclass__(cls, **kwargs):
        """add bulk_upload to the cls.Meta if it does not exist there"""
        fields = cls.Meta.fields
        if fields and 'bulk_upload' not in fields:
            cls.Meta.fields = fields + ('bulk_upload', )
        return super().__init_subclass__(**kwargs)

    @property
    def casestudy(self):
        request = self.context['request']
        url_pks = request.session.get('url_pks', {})
        casestudy_id = url_pks.get('casestudy_pk')
        if not casestudy_id:
            return None
        return Casestudy.objects.get(id=casestudy_id)

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

        df_mapped = self._map_fields(df_new)
        d_mapped = self._add_pk_relations(df_mapped)
        ret['dataframe'] = df_mapped

        return ret

    def _map_fields(self, dataframe):
        '''
        map the columns of the dataframe to the fields of the model class
        based on the field_map class attribute
        '''
        data = dataframe.copy()
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
                    missing_values = np.unique(missing[column].values)
                    # ToDo: create a file highlighting the errors in the input data
                    # will be returned as an error response
                    dataframe.set_index(self.index_column, inplace=True)
                    missing.set_index(self.index_column, inplace=True)
                    error_matrix = pd.DataFrame(
                        columns=dataframe.columns,
                        index=dataframe.index).fillna(0)
                    error_matrix.loc[
                        missing.index, 'ag'] = _('relation not found')
                    error_matrix.reset_index(inplace=True)
                    error_matrix[self.index_column] = 0
                    path, url = self._create_response_file(
                        dataframe.reset_index(),
                        errors=error_matrix,
                        file_type='tsv')
                    raise ForeignKeyNotFound(
                        _('Related models {} not found'
                          .format(missing_values)), url
                    )
            else:
                data = data.rename(columns={column: field})

        return data

    def _create_response_file(self, dataframe, errors=None, file_type='tsv'):
        '''
        creates a response file with given data

        Parameters
        ----------
        dataframe: pd.Dataframe
            the dataframe to write to file
        errors: pd.Dataframe
            same dimension as dataframe, marks errors occured in dataframe
            values - no error: nan or 0, error: error message as string

        Returns
        ----------
        path, url: tuple(str), path and relative url to file
        '''
        data = dataframe.copy()
        error_sep = '|'
        errors = errors.fillna(0)
        if errors is not None:
            data['error'] = ''
            for column in errors.columns:
                error_idx = errors[column] != 0
                data['error'][error_idx] += '{} '.format(column)
                data['error'][error_idx] += errors[column][error_idx]
                data['error'][error_idx] += error_sep

        with TemporaryMediaFile() as f:
            data.to_csv(f, sep='\t')
        return f.name, f.url


    def _add_pk_relations(self, dataframe):
        '''
        add pk related fields to dataframe
        '''
        request = self.context['request']
        url_pks = request.session.get('url_pks', {})
        for pk, rel in self.parent_lookup_kwargs.items():
            split = rel.split('__')
            # ignore chained attributes
            if len(split) > 2:
                continue
            pk = url_pks[pk]
            name = split[0]
            # get the related class of the attribute
            attr = getattr(self.Meta.model, name)
            related_model = attr.field.related_model
            obj = related_model.objects.get(id=pk)
            dataframe[name] = obj
        return dataframe

    def save_data(self, dataframe):
        """
        dataframe to models

        Parameters
        ----------
        dataframe: pd.Dataframe


        Returns
        -------
        new_models: Queryset
            models that were created
        updated_models: Queryset
            models that were updated
        """
        queryset = self.get_queryset()
        df = dataframe.set_index(self.index_column)
        df_existing = read_frame(queryset, index_col=self.index_column)

        merged = df.merge(df_existing,
                          left_index=True,
                          right_index=True,
                          how='left',
                          indicator=True,
                          suffixes=['', '_old'])

        df_new = merged.loc[merged._merge=='left_only'].reset_index()
        idx_both = merged.loc[merged._merge=='both'].index
        # update existing models with values of new data
        df_update = df_existing.loc[idx_both]
        df_update.update(df)

        new_models = self._create_models(df_new)
        updated_models = self._update_models(df_update)

        return new_models, updated_models

    def _update_models(self, dataframe):
        '''
        update the models with the data in dataframe
        '''
        queryset = self.get_queryset()
        # only fields defined in field_map will be written to database
        fields = [getattr(v, 'name', None) or v
                  for v in self.field_map.values()]
        df = dataframe.reset_index()
        updated = []

        for row in df.itertuples(index=False):
            filter_kwargs = {self.index_column: getattr(row, self.index_column)}
            model = queryset.get(**filter_kwargs)
            for c, v in row._asdict().items():
                if c not in fields:
                    continue
                setattr(model, c, v)
            model.save()
            updated.append(model)
        updated = queryset.filter(id__in=[m.id for m in updated])
        return updated

    def _create_models(self, dataframe):
        '''
        create models as described in dataframe
        '''
        model = self.Meta.model
        # skip columns, that are not needed
        field_names = [f.name for f in model._meta.fields]
        drop_cols = []
        for c in dataframe.columns:
            if not c in field_names:
                drop_cols.append(c)
        if 'id' in dataframe.columns:
            drop_cols.append('id')
        df_save = dataframe.drop(columns=drop_cols)

        # set default values for columns not provided
        defaults = {col: model._meta.get_field(col).default
                    for col in df_save.columns}
        df_save = df_save.fillna(defaults)

        # create the new rows
        bulk = []
        m = None
        for row in df_save.itertuples(index=False):
            row_dict = row._asdict()
            m = model(**row_dict)
            bulk.append(m)
        created = model.objects.bulk_create(bulk)
        return created

    def create(self, validated_data):
        '''
        overrides create()
        if file was passed -> bulk creation
        '''
        if 'dataframe' not in validated_data:
            return super().create(validated_data)
        return self.bulk_create(validated_data)

    def get_queryset(self):
        '''
        Returns
        ----------------
        QuerySet - the filtered queryset that represents the existing models to
             be updated, models will be created if not in this queryset
        '''
        raise NotImplementedError('`get_queryset()` must be implemented.')

    def bulk_create(self, validated_data):
        '''
        bulk create models based on 'dataframe' in validated_data

        Returns
        ----------------
        BulkResult
        '''
        dataframe = validated_data['dataframe']
        new, updated = self.save_data(dataframe)
        result = BulkResult(created=new, updated=updated)
        return result

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        if isinstance(instance, BulkResult):
            ret = {
                'count': len(instance.updated) + len(instance.created),
                'message': instance.message
            }
            created = ret['created'] = []
            updated = ret['updated'] = []
            for model in instance.created:
                created.append(super().to_representation(model))
            for model in instance.updated:
                updated.append(super().to_representation(model))
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

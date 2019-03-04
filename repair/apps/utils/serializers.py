from typing import Type
import pandas as pd
from django_pandas.io import read_frame
from django.db.utils import IntegrityError
from django.contrib.gis.geos.error import GEOSException
from django.contrib.gis.db.models.functions import GeoFunc
from django.db.models.fields import NOT_PROVIDED
import numpy as np
import os
import re
from django.utils.translation import ugettext as _
from tempfile import NamedTemporaryFile
from rest_framework import serializers
from django.db.models import Model
from django.db.models.fields import (IntegerField, DecimalField,
                                     FloatField, BooleanField)
from django.contrib.gis.db.models.fields import (PointField, PolygonField,
                                                 MultiPolygonField)
from django.contrib.gis.geos import GEOSGeometry, WKTWriter
from django.db.models.query import QuerySet
from django.conf import settings
from copy import deepcopy
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook

from repair.apps.asmfa.models import KeyflowInCasestudy
from repair.apps.login.models import CaseStudy


class MakeValid(GeoFunc):
    function='ST_MakeValid'


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
        os.makedirs(path)
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
    regex: str, optional
        regular expression for solving the reference, the columns of
        both sides are tried to related by the regular expression matches rather
        than the actual content
    """
    def __init__(self, name: str, referenced_field: str,
                 referenced_model: Type[Model], filter_args: dict={},
                 allow_null=False, regex=None):
        self.name = name
        self.referenced_column = referenced_field
        self.referenced_model = referenced_model
        self.filter_args = filter_args.copy()
        self.allow_null = allow_null
        self.regex = regex


    def merge(self, dataframe: pd.DataFrame, referencing_column: str,
              rel: object=None):
        """
        merges the referenced models to the given data

        Parameters
        ----------
        dataframe: pd.Dataframe
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
        data = dataframe.copy()
        # ignore the null rows
        if self.allow_null:
            data = data[data[referencing_column].notnull()]
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
        # find unique referenced values
        u_ref, counts = np.unique(np.array(referenced_queryset.values_list(
            self.referenced_column)).astype('str'), return_counts=True)
        duplicates = u_ref[counts>1]

        # only the id of the referenced queryset is relevant
        fieldnames = ['id', self.referenced_column]
        # add the keyflow, if exists for handling duplicates
        keyflow_added = False
        if 'keyflow' in [f.name for f in self.referenced_model._meta.fields]:
            fieldnames.append('keyflow')
            keyflow_added = True

        # get existing rows in the referenced table of the keyflow
        df_referenced = read_frame(referenced_queryset,
                                   fieldnames=fieldnames, verbose=False)
        df_referenced['_models'] = referenced_queryset
        # cast indices to string to avoid mismatch int <-> str
        data[referencing_column] = data[referencing_column].astype('str')
        df_referenced[self.referenced_column] = \
            df_referenced[self.referenced_column].astype('str')

        def match(x):
            matches = re.findall(self.regex, x)
            if matches:
                return matches[0]
            return x
        if self.regex:
            data[referencing_column] = data[referencing_column].apply(match)
            df_referenced[self.referenced_column] = \
                df_referenced[self.referenced_column].apply(match)

        df_referenced.set_index(self.referenced_column, inplace=True)
        # find not-unique referenced values and choose one of the duplicates
        # for merging
        u_ref, counts = np.unique(np.array(df_referenced.index),
                                  return_counts=True)
        duplicates = u_ref[counts>1]
        if len(duplicates) > 0:
            for dup_ref in duplicates:
                df_ref_wo_dup = df_referenced[df_referenced.index != dup_ref]
                df_ref_dup = df_referenced[df_referenced.index == dup_ref]
                # if a keyflow is available, prefer the ones with keyflows
                if keyflow_added:
                    w_keyflow = df_ref_dup[df_ref_dup['keyflow'].notnull()]
                    if len(w_keyflow) > 0:
                        df_ref_dup = w_keyflow
                # take the last of the remaining duplicates (that is very
                # random, but a decision has to be made)
                df_referenced = df_ref_wo_dup.append(df_ref_dup.iloc[0])

        # check if an activitygroup exist for each activity
        df_merged = data.merge(df_referenced,
                               left_on=referencing_column,
                               right_index=True,
                               how='left',
                               indicator=True,
                               suffixes=['', '_old'])

        missing_rows = df_merged.loc[df_merged._merge=='left_only']
        existing_rows = df_merged.loc[df_merged._merge=='both']

        existing_rows[referencing_column] = existing_rows['_models']

        tmp_columns = ['_merge', 'id', '_models']
        if keyflow_added:
            if 'keyflow_old' in df_merged.columns:
                tmp_columns.append('keyflow_old')
            if 'keyflow' not in dataframe.columns:
                tmp_columns.append('keyflow')
        existing_rows.drop(columns=tmp_columns, inplace=True)
        missing_rows.drop(columns=tmp_columns, inplace=True)

        # append the null rows again
        if self.allow_null:
            existing_rows = existing_rows.append(
                dataframe[dataframe[referencing_column].isnull()])
        return existing_rows, missing_rows


class ErrorMask:
    def __init__(self, dataframe):
        self.dataframe = dataframe.copy()
        self.error_matrix = pd.DataFrame(
            columns=dataframe.columns,
            index=dataframe.index).fillna(0)
        self.error_matrix.index = self.dataframe.index
        self._messages = []

    def add_message(self, msg):
        self._messages.append(msg)

    def set_error(self, indices, column, message):
        self.error_matrix.loc[indices, column] = message

    @property
    def messages(self):
        return ' - '.join(self._messages)

    @property
    def count(self):
        return (self.error_matrix != 0).sum().sum()

    def to_file(self, file_type='csv', encoding='cp1252'):
        '''
        creates a response file from errors

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
        data = self.dataframe.copy()
        error_sep = '|'
        errors = self.error_matrix.fillna(0)
        data['error'] = ''
        def highlight_errors(s, errors=None):
            column = s.name
            if column == 'error':
                return ['white'] * len(s)
            error_idx = errors[column] != 0
            return ['background-color: red' if v else
                    'white' for v in error_idx]
        if errors is not None:
            for column in errors.columns:
                error_idx = errors[column] != 0
                data['error'][error_idx] += '{}: '.format(column)
                data['error'][error_idx] += errors[column][error_idx]
                data['error'][error_idx] += error_sep
            # RangeIndex is the auto created one, we don't want that in the
            # response file
            if not isinstance(data.index, pd.RangeIndex):
                data.reset_index(inplace=True)
            if file_type == 'xlsx':
                data = data.style.apply(highlight_errors, errors=errors)

        def write(df):
            with TemporaryMediaFile() as f:
                if file_type == 'xlsx':
                    pass
                else:
                    sep = '\t' if file_type == 'tsv' else ';'
                    df.to_csv(f, sep=sep, encoding=encoding, index=False)
            if file_type == 'xlsx':
                writer = pd.ExcelWriter(f.name, engine='openpyxl')
                df.to_excel(writer, index=False)
                writer.save()
            os.chmod(f.name, 0o777)
            return f

        def encode(df):
            df = df.copy()
            for column in df.columns:
                try:
                    df[column] = df[column].apply(lambda x: x.encode(encoding))
                except:
                    pass
            return df

        # try to write file with encoding of dataframe, encode if problems occur
        try:
            f = write(data)
        except:
            data = encode(data)
            f = write(data)

        # TemporaryFile creates files with no extension,
        # keep file extension of input file
        fn = '.'.join([f.name, file_type])
        os.rename(f.name, fn)
        url = '.'.join([f.url, file_type])
        return fn, url


class BulkSerializerMixin(metaclass=serializers.SerializerMetaclass):
    bulk_upload = serializers.FileField(required=False,
                                        write_only=True)
    # important: input file will be checked if it contains those columns
    # (letter case doesn't matter, will be cast to lower case)
    field_map = {}

    # column serving as unique identifier in file
    # (letter case doesn't matter, will be cast to lower case)
    index_columns = []

    # values indicating that entry is unknown, will be set to null in model
    # (number fields only)
    nan_values = ['n.a.', '', 'NULL']

    # should index_columns be validated for uniqueness
    check_index = True

    def __init_subclass__(cls, **kwargs):
        """add bulk_upload to the cls.Meta if it does not exist there"""
        fields = cls.Meta.fields
        if fields and 'bulk_upload' not in fields:
            cls.Meta.fields = tuple(list(fields) + ['bulk_upload'])
        lower_map = {}
        # cast all keys to lower case
        for key in cls.field_map.keys():
            v = cls.field_map[key]
            lower_map[key.lower()] = v
        cls.field_map = lower_map
        cls.index_columns = [i.lower() for i in cls.index_columns]
        return super().__init_subclass__(**kwargs)

    @property
    def casestudy(self):
        request = self.context['request']
        url_pks = request.session.get('url_pks', {})
        casestudy_id = url_pks.get('casestudy_pk')
        if not casestudy_id:
            return None
        return CaseStudy.objects.get(id=casestudy_id)

    @property
    def keyflow(self):
        request = self.context['request']
        url_pks = request.session.get('url_pks', {})
        keyflow_id = url_pks.get('keyflow_pk')
        if not keyflow_id:
            return None
        return KeyflowInCasestudy.objects.get(id=keyflow_id)

    @classmethod
    def create_template(cls):
        wb = Workbook()
        ws = wb.active
        columns = []
        for c in cls.field_map.keys():
            if c in cls.index_columns:
                c += '*'
            columns.append(c)
        ws.append(columns)
        return save_virtual_workbook(wb)

    def file_to_dataframe(self, file, encoding='cp1252'):
        # remove automated validators (Uniquetogether throws error else)
        self.validators = []

        fn, ext = os.path.splitext(file.name)
        self.input_file_ext = ext
        try:
            if ext == '.xlsx':
                dataframe = pd.read_excel(file, dtype=object,
                                          keep_default_na=False,
                                          na_values=self.nan_values)
            elif ext == '.tsv':
                dataframe = pd.read_csv(file, sep='\t', encoding=encoding,
                                        dtype=object, keep_default_na=False,
                                        na_values=self.nan_values)
            elif ext == '.csv':
                dataframe = pd.read_csv(file, sep=';', encoding=encoding,
                                        dtype=object, keep_default_na=False,
                                        na_values=self.nan_values)
            else:
                raise MalformedFileError(_('unsupported filetype'))
        except pd.errors.ParserError as e:
            raise MalformedFileError(str(e))
        except UnicodeDecodeError:
            raise MalformedFileError(
                _('wrong file-encoding ({} used)'.format(encoding)))

        # pandas might set index automatically (esp. for excel files)
        dataframe.reset_index(inplace=True)
        del dataframe['index']
        dataframe = dataframe.\
            rename(columns={c: c.lower().rstrip('*')
                            for c in dataframe.columns})
        return dataframe

    def to_internal_value(self, data):
        """
        Convert csv-data to pandas dataframe and
        add it as attribute `dataframe` to the validated data
        add also `keyflow_id` to validated data
        """
        file = data.get('bulk_upload', None)
        if file is None:
            return super().to_internal_value(data)
        encoding = data.get('encoding', 'cp1252')
        self.encoding = encoding
        dataframe = self.file_to_dataframe(file, encoding=self.encoding)

        # other fields are not required when bulk uploading
        fields = self._writable_fields
        for field in fields:
            field.required = False
        ret = super().to_internal_value(data)  # would throw exc. else
        ret['dataframe'] = dataframe

        # ToDo: put this into validate()
        missing_ind = [i for i in self.index_columns if i not in
                       dataframe.columns]
        if missing_ind:
            raise MalformedFileError(
                _('Index column(s) missing: {}'.format(
                    missing_ind)))

        if self.check_index:
            df_t = dataframe.set_index(self.index_columns)
            duplicates = df_t.index.get_duplicates()
            if len(duplicates) > 0:
                if len(self.index_columns) == 1:
                    message = _('Index "{}" has to be unique!')\
                        .format(self.index_columns[0])
                else:
                    message = _('The combination of indices "{}" have to be unique!')\
                        .format(self.index_columns)
                message += ' ' + _('Duplicates found: {}').format(duplicates)
                raise ValidationError(message)
        return ret

    def parse_dataframe(self, dataframe):

        df = dataframe.copy()
        # remove all columns not in field_map (avoid conflicts when renaming)
        for column in dataframe.columns.values:
            if column not in self.field_map:
                del dataframe[column]

        self.error_mask = ErrorMask(df)
        df_mapped = self._map_fields(dataframe)
        df_parsed = self._parse_columns(df_mapped)

        if self.error_mask.count > 0:
            fn, url = self.error_mask.to_file(
                file_type=self.input_file_ext.replace('.', ''),
                encoding=self.encoding
            )
            raise ValidationError(
                self.error_mask.messages, url
            )

        df_done = self._add_pk_relations(df_parsed)

        rename = {}
        for k, v in self.field_map.items():
            if isinstance(v, Reference):
                # self referencing columns will be processed later, don't rename
                if k in self.self_refs:
                    continue
                v = v.name
            rename[k] = v

        df_done = df_done.rename(columns=rename)
        return df_done

    def _parse_int(self, x):
        try:
            return int(x)
        except:
            return np.NaN

    def _parse_float(self, x):
        if isinstance(x, str):
            n_c = x.count(',')
            n_p = x.count('.')
            if n_c + n_p > 1:
                return np.NaN
            x = x.replace(',', '.')
        try:
            return float(x)
        except:
            return np.NaN

    def _parse_bool(self, x):
        if isinstance(x, bool):
            return x
        x = x.lower()
        if x == 'true':
            return True
        elif x == 'false':
            return False
        else:
            return np.NaN

    def _parse_wkt(self, x):
        try:
            if not isinstance(x, str):
                return np.NaN
            geom = GEOSGeometry(x)
            if not geom.valid:
                return geom.valid_reason
            # force 2d
            geom2d = GEOSGeometry(self.wkt_w.write(geom))
        except GEOSException as e:
            return str(e)
        return geom2d

    def _parse_columns(self, dataframe):
        '''
        parse the columns of the input dataframe to match the data type
        of the fields
        '''
        dataframe = dataframe.copy()
        error_occured = False
        for column in dataframe.columns:
            _meta = self.Meta.model._meta
            field_name = self.field_map.get(column, None)
            if field_name is None or isinstance(field_name, Reference):
                continue
            field = _meta.get_field(field_name)
            if (isinstance(field, PointField)
                or isinstance(field, PolygonField)
                or isinstance(field, MultiPolygonField)):
                self.wkt_w = WKTWriter(dim=2)
                dataframe['wkt'] = dataframe['wkt'].apply(self._parse_wkt)
                types = dataframe['wkt'].apply(type)
                str_idx = types == str
                error_idx = dataframe.index[str_idx]
                error_msg = _('invalid geometry')
                self.error_mask.set_error(error_idx, 'wkt', error_msg)
                if len(error_idx) > 0:
                    error_occured = _('Invalid geometries')
            elif (isinstance(field, IntegerField) or
                isinstance(field, FloatField) or
                isinstance(field, DecimalField) or
                isinstance(field, BooleanField)):
                # set predefined nan-values to nan
                dataframe[column] = dataframe[column].replace(
                    self.nan_values, np.NaN)
                # parse the values (which are not nan)
                not_na = dataframe[column].notna()
                entries = dataframe[column].loc[not_na]
                if isinstance(field, IntegerField):
                    entries = entries.apply(self._parse_int)
                    error_msg = _('Integer expected: number without decimals')
                elif (isinstance(field, FloatField) or
                      isinstance(field, DecimalField)):
                    entries = entries.apply(self._parse_float)
                    error_msg = _('Float expected: number with or without '
                                  'decimals; use either "," or "." as decimal-'
                                  'seperators, no thousand-seperators allowed')
                elif isinstance(field, BooleanField):
                    entries = entries.apply(self._parse_bool)
                    error_msg = _('Boolean expected ("true" or "false")')
                # nan is used to determine parsing errors
                error_idx = entries[entries.isna()].index
                if len(error_idx) > 0:
                    error_occured = _('Number format errors')
                # set the error message in the error matrix at these positions
                self.error_mask.set_error(error_idx, column, error_msg)
                # overwrite values in dataframe with parsed ones
                dataframe[column].loc[not_na] = entries
        if error_occured:
            self.error_mask.add_message(error_occured)
        return dataframe

    def _map_fields(self, dataframe, columns=None,
                    skip_self_references=True):
        '''
        map the columns of the dataframe to the fields of the model class
        based on the field_map class attribute
        you may pass specific columns to map (then verification of missing
        columns in dataframe is skipped)
        ignores self references by default
        '''
        # detected self references (referenced model == Meta.model)
        self.self_refs = []

        data = dataframe.copy()
        if not columns:
            bulk_columns = [c.lower() for c in self.field_map.keys()]
            missing_cols = list(set(bulk_columns).difference(set(data.columns)))
            if missing_cols:
                raise MalformedFileError(
                    _('Column(s) missing: {}'.format(
                        missing_cols)))

        columns = columns or data.columns

        for column, field in self.field_map.items():
            if column not in columns:
                continue
            if isinstance(field, Reference):
                # self reference detected, handled later
                if (skip_self_references and
                (field.referenced_model == self.Meta.model)):
                    if field.allow_null == False:
                        raise Exception(
                            'self-referencing models whose self-references '
                            'are not nullable are not supported')
                    self.self_refs.append(column)
                    continue
                data, missing = field.merge(
                    data, referencing_column=column, rel=self)

                if len(missing) > 0:
                    missing_values = np.unique(missing[column].values)
                    msg = _('{c} - related models {m} not found'.format(
                        c=column, m=missing_values))
                    self.error_mask.set_error(missing.index, column,
                                              _('relation not found'))
                    self.error_mask.add_message(msg)
        return data

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
        dataframe = dataframe.reset_index()
        df_existing = read_frame(queryset, verbose=False)
        df = dataframe.copy()

        # if column is both index and referenced, we need to
        # fill it with ids, because the existing contain the ids instead
        # of models as well
        for col in self.index_columns:
            if isinstance(self.field_map[col], Reference):
                field_name = self.field_map[col].name
                df[field_name] = df[field_name].apply(
                    lambda x: x.id if hasattr(x, 'id') else x)

        for col in self.index_fields:
            df_existing[col] = df_existing[col].map(str)
            df[col] = df[col].map(str)

        merged = df.merge(df_existing,
                          how='left',
                          on=self.index_fields,
                          indicator=True,
                          suffixes=['', '_old'])

        idx_new = merged.loc[merged._merge=='left_only'].index
        idx_both = merged.loc[merged._merge=='both'].index

        df_new = dataframe.loc[idx_new]
        # update existing models with values of new data
        df_update = dataframe.loc[idx_both]

        try:
            #  map the self references now
            if self.self_refs:
                df_new_tmp = df_new.copy()
                # create models without the self-references
                for column in self.self_refs:
                    df_new_tmp[column] = None
                refs = self.self_refs.copy()
                new_models = self._create_models(df_new_tmp)
                # map the self-references on the newly created models
                df_mapped = self._map_fields(dataframe,
                                             columns=self.self_refs,
                                             skip_self_references=False)
                # check the errors occured while mapping
                if self.error_mask.count > 0:
                    # rollback on error
                    for m in new_models:
                        m.delete()
                    fn, url = self.error_mask.to_file(
                        file_type=self.input_file_ext.replace('.', ''),
                        encoding=self.encoding
                    )
                    raise ValidationError(
                        self.error_mask.messages, url
                    )
                # renaming was skipped before
                rename = {v: self.field_map[v].name for v in refs}
                df_mapped.rename(columns=rename, inplace=True)
                new_models = self._update_models(df_mapped)
                df_update = df_mapped.loc[idx_both]
            else:
                new_models = self._create_models(df_new)
            updated_models = self._update_models(df_update)
        except IntegrityError as e:
            # ToDo: formatted message
            raise ValidationError(str(e))

        return new_models, updated_models

    @property
    def index_fields(self):
        '''
        fields model-side belonging to self.index_column
        '''
        index_fields = []
        for c in self.index_columns:
            i = self.field_map.get(c, c)
            if isinstance(i, Reference):
                i = i.name
            index_fields.append(i)
        return index_fields

    def _update_models(self, dataframe):
        '''
        update the models with the data in dataframe
        '''
        model = self.Meta.model
        queryset = self.get_queryset()
        # only fields defined in field_map will be written to database
        fields = [getattr(v, 'name', None) or v
                  for v in self.field_map.values()]
        updated = []

        dataframe = self._set_defaults(dataframe, model)

        for row in dataframe.itertuples(index=False):
            filter_kwargs = {c: getattr(row, c) for c in self.index_fields}
            model = queryset.get(**filter_kwargs)
            for c, v in row._asdict().items():
                if c not in fields:
                    continue
                if type(v) in [int, float] and np.isnan(v):
                    v = None
                setattr(model, c, v)
            model.save()
            updated.append(model)
        updated = queryset.filter(id__in=[m.id for m in updated])
        return updated

    def _set_defaults(self, dataframe, model):
        # set default values for columns not provided
        defaults = {}
        for col in dataframe.columns:
            default = model._meta.get_field(col).default
            if default == NOT_PROVIDED or default is None:
                default = np.NAN
            defaults[col] = default
        return dataframe.fillna(defaults)

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
        df_save = self._set_defaults(df_save, model)

        # create the new rows
        bulk = []
        m = None
        for row in df_save.itertuples(index=False):
            #row_dict = row._asdict()
            row_dict = {}
            for k, v in row._asdict().items():
                try:
                    row_dict[k] = v if not np.isnan(v) else None
                except:
                    row_dict[k] = v
            m = model(**row_dict)
            bulk.append(m)
        try:
            created = model.objects.bulk_create(bulk)
        except ValueError:
            for m in bulk:
                m.save()
            created = bulk
        except IntegrityError as e:
            raise ValidationError(str(e))
        # only postgres returns ids after bulk creation
        # workaround for non postgres: create queryset based on index_columns
        if created and created[0].id == None:
            filter_kwargs = {}
            for field in self.index_fields:
                filter_kwargs[field + '__in'] = dataframe[field].values
            created = self.get_queryset().filter(**filter_kwargs)
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
        dataframe = self.parse_dataframe(dataframe)
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
                # bulk created objects don't retrieve their new ids
                # (at least in sqlite) -> assign one for representation after
                # creation
                if model.id is None:
                    model.id = -1
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

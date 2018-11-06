from typing import Type
import pandas as pd
from rest_framework import serializers
from django.db.models import Model
from django.db.models.query import QuerySet


class BulkSerializerMixin(metaclass=serializers.SerializerMetaclass):
    bulk_upload = serializers.FileField(required=False,
                                         write_only=True)
    def __init_subclass__(cls, **kwargs):
        """add bulk_upload to the cls.Meta if it does not exist there"""
        fields = cls.Meta.fields
        if fields and 'bulk_upload' not in fields:
            cls.Meta.fields = fields + ('bulk_upload', )

        extra_kwargs = getattr(cls.Meta, 'extra_kwargs', {})
        for field in fields:
            extra = extra_kwargs.get(field, {})
            extra['required'] = False
            extra_kwargs[field] = extra
        cls.Meta.extra_kwargs = extra_kwargs
        return super().__init_subclass__(**kwargs)

    def to_internal_value(self, data):
        """
        Convert csv-data to pandas dataframe and
        add it as attribute `dataframe` to the validated data
        add also `keyflow_id` to validated data
        """
        file = data.pop('bulk_upload', None)
        ret = super().to_internal_value(data)
        if file is None:
            return ret

        encoding = 'cp1252'
        df_new = pd.read_csv(file[0], sep='\t', encoding=encoding)
        df_new = df_new.\
            rename(columns={c: c.lower() for c in df_new.columns})
        ret['dataframe'] = df_new
        request = self.context['request']
        url_pks = request.session.get('url_pks', {})
        keyflow_id = url_pks.get('keyflow_pk')
        ret['keyflow_id'] = keyflow_id
        return ret

    def create(self, validated_data):
        if 'dataframe' not in validated_data:
            return super().create(validated_data)
        return self.bulk_create(validated_data)

    def bulk_create(self, validated_data):
        '''
        bulk create models based on 'dataframe' in validated_data

        Return
        ----------------
        queryset of all created/updated models
        '''
        raise NotImplementedError('`bulk_create()` must be implemented.')

    def check_foreign_keys(self,
                           df_new: pd.DataFrame,
                           referenced_table: Type[Model],
                           referencing_column: str,
                           filter_value: int,
                           referenced_column: str='code',
                           filter_expr: str='keyflow_id',
                           ):
        """
        check foreign key in referenced table

        Parameters
        ----------
        df_new: pd.Dataframe
            the dataframe with the rows to check
        referenced_table: Model-Class
            the referenced Model
        referencing_column: str
            the referencing column in df_new that should be checked
        filter_value: int
            the value like the keyflow_id to filter the referencing table
        referenced_column: str, optional(default='code')
            the referenced column to search in
        filter_expr: str, optional(default='keyflow_id')
            the filter-expression like keyflow_id to filter the values in the
            referenced_table

        Returns
        -------
        existing_keys: pd.Dataframe
            the merged dataframe
        missing_rows: pd.Dataframe
            the rows in the df_new where rows are missing
        """
        # get existing rows in the referenced table of the keyflow
        qs = referenced_table.objects.filter(keyflow_id=kic.id)
        df_referenced = read_frame(qs, index_col=[referenced_column])

        index_col = 'code'

        # check if an activitygroup exist for each activity
        df_merged = df_new.merge(df_referenced,
                                 left_on=referencing_column,
                                 right_index=True,
                                 how='left',
                                 indicator=True,
                                 suffixes=['', '_old'])
        missing_rows = df_merged.loc[df_merged._merge=='left_only']
        existing_rows = df_merged.loc[df_merged._merge=='both']
        return existing_rows, missing_rows
    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        if isinstance(instance, QuerySet):
            ret = {
                'count': len(instance),
            }
            results = ret['results'] = []
            for model in instance:
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

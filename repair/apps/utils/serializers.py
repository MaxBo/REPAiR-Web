import pandas as pd
from rest_framework import serializers


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
        has to return what?
        '''
        raise NotImplementedError('`bulk_create()` must be implemented.')


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

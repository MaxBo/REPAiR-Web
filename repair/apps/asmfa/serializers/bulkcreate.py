from django.utils.translation import ugettext as _
import numpy as np

from repair.apps.utils.serializers import (BulkSerializerMixin,
                                           BulkResult,
                                           Reference,
                                           ValidationError,
                                           ErrorMask)
from repair.apps.asmfa.serializers import (ActivityGroupSerializer,
                                           ActivitySerializer,
                                           ActorSerializer,
                                           Actor2ActorSerializer,
                                           ActorStockSerializer,
                                           AdministrativeLocationSerializer,
                                           ProductSerializer,
                                           WasteSerializer,
                                           MaterialSerializer,
                                           ProductFractionSerializer
                                           )
from repair.apps.asmfa.models import (KeyflowInCasestudy,
                                      ActivityGroup,
                                      Activity,
                                      Actor,
                                      Actor2Actor,
                                      ActorStock,
                                      Composition,
                                      AdministrativeLocation,
                                      Material,
                                      Product,
                                      Waste,
                                      ProductFraction,
                                      Process
                                      )
from repair.apps.publications.models import PublicationInCasestudy


class ActivityGroupCreateSerializer(BulkSerializerMixin,
                                    ActivityGroupSerializer):

    field_map = {
        'code': 'code',
        'name': 'name'
    }
    index_columns = ['code']

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
    index_columns = ['nace']

    def get_queryset(self):
        return Activity.objects.filter(activitygroup__keyflow=self.keyflow)


class ActorCreateSerializer(BulkSerializerMixin,
                            ActorSerializer):

    field_map = {
        'BvDid': 'BvDid',
        'name': 'name',
        'code': 'consCode',
        'year': 'year',
        'description english': 'description_eng',
        'description original': 'description',
        'BvDii': 'BvDii',
        'website': 'website',
        'employees': 'employees',
        'turnover': 'turnover',
        'nace': Reference(
            name='activity',
            referenced_field='nace',
            referenced_model=Activity,
#            regex='[0-9]+',
            filter_args={'activitygroup__keyflow': '@keyflow'}
        )
    }
    index_columns = ['BvDid']

    def get_queryset(self):
        return Actor.objects.filter(
            activity__activitygroup__keyflow=self.keyflow)


class Actor2ActorCreateSerializer(BulkSerializerMixin,
                                  Actor2ActorSerializer):

    field_map = {
        'origin': Reference(name='origin',
                            referenced_field='BvDid',
                            referenced_model=Actor,
                            filter_args={
                                'activity__activitygroup__keyflow':
                                '@keyflow'}),
        'destination': Reference(name='destination',
                                 referenced_field='BvDid',
                                 referenced_model=Actor,
                                 filter_args={
                                     'activity__activitygroup__keyflow':
                                     '@keyflow'}),
        'composition': Reference(name='composition',
                                 referenced_field='name',
                                 referenced_model=Composition),
        'source': Reference(name='publication',
                            referenced_field='publication__citekey',
                            referenced_model=PublicationInCasestudy,
                            filter_args={'casestudy': '@casestudy'}),
        'process': Reference(name='process', referenced_field='name',
                             referenced_model=Process,
                             allow_null=True),
        'waste': 'waste',
        'amount': 'amount',
        'year': 'year'
    }
    index_columns = ['origin', 'destination', 'composition']

    def get_queryset(self):
        return Actor2Actor.objects.filter(keyflow=self.keyflow)

    def validate(self, attrs):
        if 'dataframe' in attrs:
            df = attrs['dataframe']
            self_ref = df['origin'] == df['destination']

            if self_ref.sum() > 0:
                message = _("Flows from an actor to itself are not allowed.")
                error_mask = ErrorMask(df)
                error_mask.set_error(df.index[self_ref], 'destination', message)
                fn, url = error_mask.to_file(
                    file_type=self.input_file_ext.replace('.', ''),
                    encoding=self.encoding
                )
                error_mask.add_message(message)
                raise ValidationError(
                    error_mask.messages, url
                )
        return super().validate(attrs)

    def _create_models(self, df):
        created = super()._create_models(df)
        # trigger conversion to fraction flow
        for model in created:
            model.save()
        return created


class ActorStockCreateSerializer(BulkSerializerMixin,
                                 ActorStockSerializer):

    field_map = {
        'origin': Reference(name='origin',
                            referenced_field='BvDid',
                            referenced_model=Actor,
                            filter_args={
                                'activity__activitygroup__keyflow':
                                '@keyflow'}),
        'composition': Reference(name='composition',
                                 referenced_field='name',
                                 referenced_model=Composition),
        'source': Reference(name='publication',
                            referenced_field='publication__citekey',
                            referenced_model=PublicationInCasestudy,
                            filter_args={'casestudy': '@casestudy'}),
        'amount': 'amount',
        'year': 'year',
        'waste': 'waste'
    }
    index_columns = ['origin', 'composition']

    def get_queryset(self):
        return ActorStock.objects.filter(keyflow=self.keyflow)

    def _create_models(self, df):
        created = super()._create_models(df)
        # trigger conversion to fraction flow
        for model in created:
            model.save()
        return created


class AdminLocationCreateSerializer(
    BulkSerializerMixin, AdministrativeLocationSerializer):

    field_map = {
        'BvDid': Reference(name='actor',
                           referenced_field='BvDid',
                           referenced_model=Actor,
                           filter_args={
                               'activity__activitygroup__keyflow':
                               '@keyflow'}),
        'Postcode': 'postcode',
        'Address': 'address',
        'City': 'city',
        'WKT': 'geom'
    }
    index_columns = ['BvDid']

    def get_queryset(self):
        return AdministrativeLocation.objects.filter(
            actor__activity__activitygroup__keyflow=self.keyflow)


class MaterialCreateSerializer(BulkSerializerMixin, MaterialSerializer):
    field_map = {
        'parent': Reference(name='parent',
                            referenced_field='name',
                            referenced_model=Material,
                            allow_null=True),
        'name': 'name',
    }
    index_columns = ['name']

    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }

    def get_queryset(self):
        return Material.objects.filter(keyflow=self.keyflow)


class FractionCreateSerializer(BulkSerializerMixin, ProductFractionSerializer):

    field_map = {
        'name': Reference(name='composition',
                          referenced_field='name',
                          referenced_model=Composition,
                          filter_args={'keyflow': '@keyflow'}),
        'fraction': 'fraction',
        'material': Reference(name='material',
                              referenced_field='name',
                              referenced_model=Material,
                              allow_null=True),
        'avoidable': 'avoidable',
        'hazardous': 'hazardous',
        'source': Reference(name='publication',
                            referenced_field='publication__citekey',
                            referenced_model=PublicationInCasestudy,
                            filter_args={'casestudy': '@casestudy'})
        }

    def get_queryset(self):
        return ProductFraction.objects.all()

    # ToDo: implement general validators @BulkSerializerMixin
    def _validate_fractions(self, dataframe):
        '''
        check if fractions per composition sum up to 1
        '''
        index = 'composition'
        df = dataframe.filter([index, 'fraction'])
        grouped = df.groupby(index).agg('sum')
        isclose = np.isclose(grouped['fraction'], 1, atol=0.01)
        invalid = np.invert(isclose)
        if invalid.sum() > 0:
            message = _("fractions per composition have to sum up to 1.0 with "
                        "an absolute tolerance of 0.01 "
                        "(they don't)")
            invalid_comp = grouped.index[invalid]
            for comp in invalid_comp:
                indices = dataframe[dataframe[index] == comp].index
                self.error_mask.set_error(indices, 'fraction', message)
            fn, url = self.error_mask.to_file(
                file_type=self.input_file_ext.replace('.', ''),
                encoding=self.encoding
            )
            self.error_mask.add_message(message)
            raise ValidationError(
                self.error_mask.messages, url
            )


class CompositionCreateMixin:
    check_index = False

    def bulk_create(self, validated_data):
        index = 'name'
        dataframe = validated_data['dataframe']
        df_comp = self.parse_dataframe(dataframe.copy())
        df_comp = df_comp[df_comp[index].notnull()]
        df_comp.drop_duplicates(keep='first', inplace=True)
        df_comp.reset_index(inplace=True)
        del df_comp['index']
        new_comp, updated_comp = self.save_data(df_comp)
        # drop all existing fractions of the compositions
        ids = [m.id for m in updated_comp]
        existing_fractions = ProductFraction.objects.filter(
            composition__id__in = ids)
        existing_fractions.delete()
        # process the fractions
        df_fract = dataframe.copy()
        df_fract[index] = dataframe[index].fillna(method='ffill')
        df_fract['nace'] = dataframe['nace'].fillna(method='ffill')
        fraction_serializer = FractionCreateSerializer()
        fraction_serializer.input_file_ext = self.input_file_ext
        fraction_serializer.encoding = self.encoding
        fraction_serializer._context = self.context
        df_fract = fraction_serializer.parse_dataframe(df_fract)
        # take error mask with original dataframe
        # (not the floodfilled one of FractionSerializer, better error response)
        fraction_serializer.error_mask = self.error_mask
        fraction_serializer._validate_fractions(df_fract)
        fraction_serializer._create_models(df_fract)
        result = BulkResult(created=new_comp, updated=updated_comp)
        return result


class WasteCreateSerializer(CompositionCreateMixin, BulkSerializerMixin,
                            WasteSerializer):

    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }

    field_map = {
        'name': 'name',
        'nace': 'nace',
        #'ewc':
        #'hazardous',
        #'Item_descr': ''
    }
    index_columns = ['name']

    def get_queryset(self):
        return Waste.objects.filter(keyflow=self.keyflow)


class ProductCreateSerializer(CompositionCreateMixin, BulkSerializerMixin,
                              ProductSerializer):

    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }

    field_map = {
        'name': 'name',
        'nace': 'nace'
    }
    index_columns = ['name']

    def get_queryset(self):
        return Product.objects.filter(keyflow=self.keyflow)

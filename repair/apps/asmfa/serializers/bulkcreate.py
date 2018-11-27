from repair.apps.utils.serializers import (BulkSerializerMixin,
                                           BulkResult,
                                           Reference)
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
                                      ProductFraction
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
    index_columns = ['BvD ID number']

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
                            referenced_model=PublicationInCasestudy),
        'amount': 'amount',
        'year': 'year'
    }
    index_columns = ['origin', 'destination']

    def get_queryset(self):
        return Actor2Actor.objects.filter(keyflow=self.keyflow)


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
                            referenced_model=PublicationInCasestudy),
        'amount': 'amount',
        'year': 'year'
    }
    index_columns = ['origin']

    def get_queryset(self):
        return ActorStock.objects.filter(keyflow=self.keyflow)


class AdminLocationCreateSerializer(
    BulkSerializerMixin, AdministrativeLocationSerializer):

    field_map = {
        'BvDIDNR': Reference(name='actor',
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
    index_columns = ['BvDIDNR']

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
        'source': Reference(name='publication',
                            referenced_field='publication__citekey',
                            referenced_model=PublicationInCasestudy)
        }

    def get_queryset(self):
        return ProductFraction.objects.all()


class CompositionCreateMixin:

    def bulk_create(self, validated_data):
        index = 'name'
        dataframe = validated_data['dataframe']
        df_comp = self.parse_dataframe(dataframe.copy())
        df_comp = df_comp[df_comp[index].notnull()]
        df_comp.reset_index(inplace=True)
        del df_comp['index']
        df_comp.drop_duplicates(keep='first', inplace=True)
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

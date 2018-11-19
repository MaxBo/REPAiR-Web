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
                                           ActorSerializer,
                                           Actor2ActorSerializer,
                                           ActorStockSerializer,
                                           AdministrativeLocationSerializer,
                                           ProductSerializer,
                                           WasteSerializer,
                                           MaterialSerializer
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
                                      Waste
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
                            # ToDo: materials can relate to materials without any
                            # keyflow, how to handle name duplicates caused
                            # by keyflow related materials?
                            #filter_args={'keyflow': '@keyflow'},
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


class ProductCreateSerializer(
    BulkSerializerMixin, ProductSerializer):

    parent_lookup_kwargs = {
        'casestudy_pk': 'keyflow__casestudy__id',
        'keyflow_pk': 'keyflow__id',
    }

    def get_queryset(self):
        return Product.objects.filter(keyflow=self.keyflow)

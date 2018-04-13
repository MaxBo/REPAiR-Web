from abc import ABC

from django.shortcuts import get_object_or_404
from django.db.models.sql.constants import QUERY_TERMS

from rest_framework import exceptions

from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnDict


from repair.apps.login.models import CaseStudy


class CasestudyReadOnlyViewSetMixin(ABC):
    """
    This Mixin provides general list and create methods filtering by
    lookup arguments and query-parameters matching fields of the requested objects

    class-variables
    --------------
       casestudy_only - if True, get only items of the current casestudy
       additional_filters - dict, keyword arguments for additional filters
    """
    casestudy_only = True
    additional_filters = {}
    serializer_class = None
    serializers = {}
    pagination_class = None

    def get_serializer_class(self):
        return self.serializers.get(self.action,
                                    self.serializer_class)

    def check_casestudy(self, kwargs, request):
        """check if user has permission to access the casestudy and
        set the casestudy as a session attribute if its in the kwargs"""
        # anonymous if not logged in
        user_id = -1 if request.user.id is None else request.user.id
        # pk if route is /api/casestudies/ else casestudy_pk
        casestudy_id = kwargs.get('casestudy_pk') or kwargs.get('pk')
        try:
            casestudy = CaseStudy.objects.get(id=casestudy_id)
            if not casestudy.userincasestudy_set.all().filter(user__id=user_id):
                raise exceptions.PermissionDenied()
        except CaseStudy.DoesNotExist:
            # maybe casestudy is about to be posted-> go on
            pass
        # check if user is in casestudy, raise exception, if not
        request.session['url_pks'] = kwargs

    def list(self, request, **kwargs):
        """
        filter the queryset with the lookup-arguments
        and then render the filtered queryset with the serializer
        the lookup-arguments are defined in the "parent_lookup_kwargs" of the
        Serializer-Class
        """
        self.check_permission(request, 'view')
        SerializerClass = self.get_serializer_class()
        if self.casestudy_only:
            self.check_casestudy(kwargs, request)
        queryset = self._filter(kwargs, query_params=request.query_params,
                                SerializerClass=SerializerClass)
        if queryset is None:
            return Response(status=400)
        if self.pagination_class:
            paginator = self.pagination_class()
            queryset = paginator.paginate_queryset(queryset, request)
            
        serializer = SerializerClass(queryset, many=True,
                                     context={'request': request, })
            
        data = self.filter_fields(serializer, request)
        if self.pagination_class:
            return paginator.get_paginated_response(data)
        return Response(data)

    def retrieve(self, request, **kwargs):
        """
        filter the queryset with the lookup-arguments
        and then render the filtered queryset with the serializer
        the lookup-arguments are defined in the "parent_lookup_kwargs" of the
        Serializer-Class
        """
        self.check_permission(request, 'view')
        SerializerClass = self.get_serializer_class()
        if self.casestudy_only:
            self.check_casestudy(kwargs, request)
        pk = kwargs.pop('pk')
        queryset = self._filter(kwargs, query_params=request.query_params,
                                SerializerClass=SerializerClass)
        model = get_object_or_404(queryset, pk=pk)
        serializer = SerializerClass(model, context={'request': request})
        data = self.filter_fields(serializer, request)
        return Response(data)

    @staticmethod
    def filter_fields(serializer, request):
        """
        limit amount of fields of response by optional query parameter 'field'
        """
        data = serializer.data
        fields = request.query_params.getlist('field')
        if fields:
            if isinstance(data, ReturnDict):
                data = {k: v for k, v in data.items() if k in fields}
            else:
                data = [{k: v for k, v in row.items() if k in fields}
                        for row in data]
        return data

    def _filter(self, lookup_args, query_params=None, SerializerClass=None):
        """
        return a queryset filtered by lookup arguments and query parameters
        return None if query parameters are malformed
        """
        SerializerClass = SerializerClass or self.get_serializer_class()
        # filter the lookup arguments
        filter_args = {v: lookup_args[k] for k, v
                       in SerializerClass.parent_lookup_kwargs.items()}

        # filter additional expressions
        filter_args.update(self.get_filter_args(queryset=self.get_queryset(),
                                                query_params=query_params)
                           )
        queryset = self.get_queryset().filter(**filter_args)

        return queryset

    def get_filter_args(self, queryset, query_params=None):
        """
        get filter arguments defined by the query_params
        and by additional filters
        """
        # filter any query parameters matching fields of the model
        filter_args = {k: v for k, v in self.additional_filters.items()}
        if not query_params:
            return filter_args
        for k, v in query_params.items():
            key_cmp = k.split('__')
            key = key_cmp[0]
            if hasattr(queryset.model, key):
                if len(key_cmp) > 1:
                    cmp = key_cmp[-1]
                    if cmp not in QUERY_TERMS:
                        continue
                    if cmp == 'in':
                        v = v.strip('[]').split(',')
                filter_args[k] = v
        return filter_args


class CasestudyViewSetMixin(CasestudyReadOnlyViewSetMixin):
    """
    This Mixin provides general list and create methods filtering by
    lookup arguments and query-parameters matching fields of the requested objects

    class-variables
    --------------
       casestudy_only - if True, get only items of the current casestudy
       additional_filters - dict, keyword arguments for additional filters
    """
    def create(self, request, **kwargs):
        """set the """
        if self.casestudy_only:
            self.check_casestudy(kwargs, request)
        return super().create(request, **kwargs)

    def perform_create(self, serializer):
        url_pks = serializer.context['request'].session['url_pks']
        new_kwargs = {}
        for k, v in url_pks.items():
            key = self.serializer_class.parent_lookup_kwargs[k].replace('__id', '_id')
            if '__' in key:
                continue
            new_kwargs[key] = v
        serializer.save(**new_kwargs)


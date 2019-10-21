from rest_framework import viewsets, exceptions, mixins , status
from django.views import View
from django.http import (HttpResponseBadRequest,
                         HttpResponse,
                         HttpResponseForbidden,
                         JsonResponse,
                         )
from django.db.models import ProtectedError
from django.utils.translation import ugettext as _
from publications_bootstrap.models import Publication
from repair.apps.login.serializers import PublicationSerializer
from abc import ABC

from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnDict
from repair.apps.login.models import CaseStudy
from repair.apps.utils.serializers import (BulkValidationError,
                                           BulkSerializerMixin)


class PostGetViewMixin:
    """
    mixin for querying resources with POST method to be able to put parameters
    into the body,
    the query parameter 'GET=true' when posting signals derived views to call
    post_get function to look into the body for parameters and to behave like
    when receiving a GET request (no creation of objects then)
    WARNING: contradicts the RESTful API, so use only when query parameters
    are getting too big (browsers have technical restrictions for the
    length of an url)
    """
    def create(self, request, **kwargs):
        if self.isGET:
            return self.post_get(request, **kwargs)
        return super().create(request, **kwargs)

    @property
    def isGET(self):
        if self.request.method == 'GET':
            return True
        post_get = self.request.query_params.get('GET', False)
        if (post_get and post_get in ['True', 'true']):
            return True
        return False

    def post_get(self, request, **kwargs):
        """
        override this, should return serialized data of requested resources
        """
        return super().list(request, **kwargs)


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
            casestudy = CaseStudy.objects.defer('geom', 'focusarea').get(id=casestudy_id)
            if not casestudy.userincasestudy_set.all().filter(user__id=user_id):
                raise exceptions.PermissionDenied()
        except CaseStudy.DoesNotExist:
            # maybe casestudy is about to be posted-> go on
            pass
        # check if user is in casestudy, raise exception, if not
        request.session['url_pks'] = kwargs

    def list(self, request, **kwargs):
        self.check_permission(request, 'view')
        SerializerClass = self.get_serializer_class()
        if self.casestudy_only:
            self.check_casestudy(kwargs, request)

        # special format requested -> let the plugin handle that
        if ('format' in request.query_params):
            return super().list(request, **kwargs)

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

    def _filter(self, lookup_args, query_params=None, SerializerClass=None,
                annotations=None):
        """
        return a queryset filtered by lookup arguments and query parameters
        return None if query parameters are malformed
        """
        SerializerClass = SerializerClass or self.get_serializer_class()
        # filter the lookup arguments
        filter_args = {v: lookup_args[k] for k, v
                       in SerializerClass.parent_lookup_kwargs.items()}

        queryset = self.get_queryset()
        # filter additional expressions
        filter_args.update(self.get_filter_args(queryset=queryset,
                                                query_params=query_params)
                           )
        queryset = queryset.filter(**filter_args)

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
            is_attr = (hasattr(queryset.model, key) or
                       key in queryset.query.annotations)
            if is_attr:
                if len(key_cmp) > 1:
                    cmp = key_cmp[-1]
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
        """check permission for casestudy"""
        if self.casestudy_only:
            self.check_casestudy(kwargs, request)
        try:
            return super().create(request, **kwargs)
        except BulkValidationError as e:
            return self.error_response(e.message, file_url=e.path)

    def error_response(self, message, file_url=None):
        res = { 'message': message }
        if file_url:
            res['file_url'] = file_url
        response = JsonResponse(res, status=400)
        return response

    def perform_create(self, serializer):
        url_pks = serializer.context['request'].session['url_pks']
        new_kwargs = {}
        for k, v in url_pks.items():
            if k not in self.serializer_class.parent_lookup_kwargs:
                continue
            key = self.serializer_class.parent_lookup_kwargs[k].replace('__id', '_id')
            if '__' in key:
                continue
            new_kwargs[key] = v
        serializer.save(**new_kwargs)

    def list(self, request, **kwargs):
        if request.query_params.get('request', None) == 'template':
            serializer = self.serializers.get('create', None)
            if serializer and hasattr(serializer, 'create_template'):
                content = serializer.create_template()
                response = HttpResponse(
                    content_type=(
                        'application/vnd.openxmlformats-officedocument.'
                        'spreadsheetml.sheet'
                    )
                )
                response['Content-Disposition'] = \
                    'attachment; filename=template.xlsx'
                response.write(content)
                return response
        return super().list(request, **kwargs)


class CheckPermissionMixin:

    def check_permission(self, request, permission_name):
        """
        Check if the user has the right permission for the request. If not:
        Throw PermissionDenied() exception
        """
        # get permission code for the model
        app_label = self.serializer_class.Meta.model._meta.app_label
        view_name = self.serializer_class.Meta.model._meta.object_name
        permission = '{}.{}_{}'.format(app_label.lower(),
                                       permission_name,
                                       view_name.lower())
        # check if user has the required permission
        if not request.user.has_perm(permission):
            raise exceptions.PermissionDenied()


class ModelReadPermissionMixin(CheckPermissionMixin):

    def list(self, request, **kwargs):
        """
        Check if user is permitted for list view.
        """
        self.check_permission(request, 'view')
        return super().list(request, **kwargs)

    def retrieve(self, request, **kwargs):
        """
        Check if user is permitted for detail view.
        """
        self.check_permission(request, 'view')
        return super().retrieve(request, **kwargs)


class ModelWritePermissionMixin(CheckPermissionMixin):

    def create(self, request, **kwargs):
        """
        Check if user is permitted to create this object.
        """
        self.check_permission(request, 'add')
        return super().create(request, **kwargs)

    def destroy(self, request, **kwargs):
        """
        Check if user is permitted to destroy the object.
        """
        # param to override protection may be in the url or inside the form data
        override_protection = request.query_params.get(
            'override_protection', False) or request.data.get(
            'override_protection', False)
        self.use_protection = override_protection not in ('true', 'True', True)
        self.check_permission(request, 'delete')
        try:
            response = super().destroy(request, **kwargs)
        except ProtectedError as err:
            qs = err.protected_objects
            show = 5
            n_objects = qs.count()
            msg_n_referenced = '{} {}:'.format(n_objects,
                                               _('Referencing Object(s)')
                                               )
            msg = '<br/>'.join(list(err.args[:1]) +
                               [msg_n_referenced] +
                               [repr(row).strip('<>') for row in qs[:show]] +
                               ['...' if n_objects > show else '']
                               )
            return HttpResponseForbidden(content=msg)
        return response

    def perform_destroy(self, instance):
        instance.delete(use_protection=self.use_protection)

    def update(self, request, **kwargs):
        """
        Check if user is permitted to update the object.
        """
        self.check_permission(request, 'change')
        return super().update(request, **kwargs)

    def partial_update(self, request, **kwargs):
        """
        Check if user is permitted to partial_update the object.
        """
        self.check_permission(request, 'change')
        return super().partial_update(request, **kwargs)


class ModelPermissionViewSet(ModelReadPermissionMixin,
                             ModelWritePermissionMixin,
                             viewsets.ModelViewSet):
    """
    Check if a user has the required permissions for create(), delete(),
    update(), retrieve() and list(). Throw exceptions.PermissionDenied() if
    permission is missing.
    """


class PublicationView(ModelPermissionViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    pagination_class = None


class ReadUpdateViewSet(mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    """
    A viewset that provides default `retrieve()`, `update()`,
    `partial_update()`,  and `list()` actions.
    No `create()` or `destroy()`
    """


class ReadUpdatePermissionViewSet(mixins.RetrieveModelMixin,
                                  mixins.UpdateModelMixin,
                                  mixins.ListModelMixin,
                                  viewsets.GenericViewSet):
    """
    Check if a user has the required permissions for update(), retrieve() and
    list(). Throw exceptions.PermissionDenied() if permission is missing.
    """
    def check_permission(self, request, permission_name):
        """
        Check if the user has the right permission for the request. If not:
        Throw PermissionDenied() exception
        """
        # get permission code for the model
        app_label = self.serializer_class.Meta.model._meta.app_label
        view_name = self.serializer_class.Meta.model._meta.object_name
        permission = '{}.{}_{}'.format(app_label.lower(),
                                       permission_name, view_name.lower())
        # check if user has the required permission
        if not request.user.has_perm(permission):
            raise exceptions.PermissionDenied()

    def list(self, request, **kwargs):
        """
        Check if user is permitted for list view.
        """
        self.check_permission(request, 'view')
        return super().list(request, **kwargs)

    def retrieve(self, request, **kwargs):
        """
        Check if user is permitted for detail view.
        """
        self.check_permission(request, 'view')
        return super().retrieve(request, **kwargs)

    def update(self, request, **kwargs):
        """
        Check if user is permitted to update the object.
        """
        self.check_permission(request, 'change')
        return super().update(request, **kwargs)

    def partial_update(self, request, **kwargs):
        """
        Check if user is permitted to partial_update the object.
        """
        self.check_permission(request, 'change')
        return super().partial_update(request, **kwargs)

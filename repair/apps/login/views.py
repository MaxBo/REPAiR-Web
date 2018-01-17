from abc import ABC

from django.shortcuts import render
from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404
from django.views import View
from django.http import HttpResponseRedirect, JsonResponse
from django.db.models.sql.constants import QUERY_TERMS
from publications_bootstrap.models import Publication

from rest_framework import viewsets, mixins, exceptions

from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnDict

from reversion.views import RevisionMixin

from repair.apps.login.models import Profile, CaseStudy, UserInCasestudy
from repair.apps.login.serializers import (UserSerializer,
                                           GroupSerializer,
                                           CaseStudySerializer,
                                           UserInCasestudySerializer,
                                           PublicationSerializer)


class CasestudyViewSetMixin(ABC):
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
            if len(casestudy.userincasestudy_set.all().filter(user__id=user_id)) == 0:
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
        SerializerClass = self.get_serializer_class()
        if self.casestudy_only:
            self.check_casestudy(kwargs, request)
        queryset = self._filter(kwargs, query_params=request.query_params,
                                SerializerClass=SerializerClass)
        if queryset is None:
            return Response(status=400)
        serializer = SerializerClass(queryset, many=True,
                                     context={'request': request, })
        data = self.filter_fields(serializer, request)
        return Response(data)

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


    def retrieve(self, request, **kwargs):
        """
        filter the queryset with the lookup-arguments
        and then render the filtered queryset with the serializer
        the lookup-arguments are defined in the "parent_lookup_kwargs" of the
        Serializer-Class
        """
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

    def filter_fields(self, serializer, request):
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

    def _filter(self, lookup_args, query_params={}, SerializerClass=None):
        """
        return a queryset filtered by lookup arguments and query parameters
        return None if query parameters are malformed
        """
        SerializerClass = SerializerClass or self.get_serializer_class()
        # filter the lookup arguments
        filter_args = {v: lookup_args[k] for k, v
                       in SerializerClass.parent_lookup_kwargs.items()}

        # filter additional expressions
        filter_args.update(self.get_filter_args(queryset=self.queryset,
                                                query_params=query_params)
                           )
        try:
            queryset = self.queryset.model.objects.filter(**filter_args)
        except Exception as e:
            # ToDo: ExceptionHandling is very broad. Pleas narrow down!
            print(e)
            return None
        return queryset

    def get_filter_args(self, queryset, query_params):
        """
        get filter arguments defined by the query_params
        and by additional filters
        """
        # filter any query parameters matching fields of the model
        filter_args = {k: v for k, v in self.additional_filters.items()}
        for k, v in query_params.items():
            key_cmp = k.split('__')
            key = key_cmp[0]
            if hasattr(queryset.model, key):
                if len(key_cmp) > 1:
                    cmp = key_cmp[-1]
                    if cmp not in QUERY_TERMS:
                        continue
                filter_args[k] = v
        return filter_args


class OnlySubsetMixin(CasestudyViewSetMixin):
    """"""
    def set_casestudy(self, kwargs, request):
        """set the casestudy as a session attribute if its in the kwargs"""
        request.session['url_pks'] = kwargs


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class CaseStudyViewSet(RevisionMixin, CasestudyViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows casestudy to be viewed or edited.
    """
    queryset = CaseStudy.objects.all()
    serializer_class = CaseStudySerializer

    def list(self, request, **kwargs):
        user_id = -1 if request.user.id is None else request.user.id
        casestudies = set()
        for casestudy in self.queryset:
            if len(casestudy.userincasestudy_set.all().filter(user__id=user_id)):
                casestudies.add(casestudy)
        serializer = self.serializer_class(casestudies, many=True,
                                           context={'request': request, })
        return Response(serializer.data)


class UserInCasestudyViewSet(CasestudyViewSetMixin,
                             mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.ListModelMixin,
                             viewsets.GenericViewSet):
    """
    API endpoint that allows userincasestudy to be viewed or edited.
    """
    queryset = UserInCasestudy.objects.all()
    serializer_class = UserInCasestudySerializer


###############################################################################
###   views for the templates

class SessionView(View):
    def post(self, request):
        if request.POST['casestudy']:
            request.session['casestudy'] = request.POST['casestudy']
            next = request.POST.get('next', '/')
            return HttpResponseRedirect(next)

    def get(self, request):
        response =  {'casestudy': request.session.get('casestudy')}
        return JsonResponse(response)


class PublicationView(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    pagination_class = None
from abc import ABC

from django.shortcuts import render
from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404
from django.views import View
from django.http import HttpResponseRedirect, JsonResponse

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnDict

from reversion.views import RevisionMixin

from repair.apps.login.models import Profile, CaseStudy, UserInCasestudy
from repair.apps.login.serializers import (UserSerializer,
                                           GroupSerializer,
                                           CaseStudySerializer,
                                           UserInCasestudySerializer)


class ViewSetMixin(ABC):
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

    def set_casestudy(self, kwargs, request):
        """set the casestudy as a session attribute if its in the kwargs"""
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
            self.set_casestudy(kwargs, request)
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
            self.set_casestudy(kwargs, request)
        return super().create(request, **kwargs)

    def retrieve(self, request, **kwargs):
        """
        filter the queryset with the lookup-arguments
        and then render the filtered queryset with the serializer
        the lookup-arguments are defined in the "parent_lookup_kwargs" of the
        Serializer-Class
        """
        SerializerClass = self.get_serializer_class()
        if self.casestudy_only:
            self.set_casestudy(kwargs, request)
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
        # filter any query parameters matching fields of the model
        for k, v in query_params.items():
            if hasattr(self.queryset.model, k):
                filter_args[k] = v
        try:
            queryset = self.queryset.model.objects.filter(**filter_args)
        except Exception as e:
            print(e)
            return None

        if len(self.additional_filters):
            queryset = queryset.filter(**self.additional_filters)
        return queryset



class OnlySubsetMixin(ViewSetMixin):
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


class CaseStudyViewSet(RevisionMixin, ViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows casestudy to be viewed or edited.
    """
    queryset = CaseStudy.objects.all()
    serializer_class = CaseStudySerializer

    def list(self, request, **kwargs):
        user_id = request.user.id or -1
        casestudies = set()
        for casestudy in self.queryset:
            if len(casestudy.userincasestudy_set.all().filter(user__id=user_id)):
                casestudies.add(casestudy)
        serializer = self.serializer_class(casestudies, many=True,
                                           context={'request': request, })
        return Response(serializer.data)


class UserInCasestudyViewSet(ViewSetMixin, viewsets.ModelViewSet):
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


def casestudy(request, casestudy_id):
    """casestudy view"""
    casestudy = CaseStudy.objects.get(pk=casestudy_id)
    stakeholdercategories = casestudy.stakeholdercategory_set.all()
    users = casestudy.user_set.all()
    solution_categories = casestudy.solution_categories

    context = {
        'casestudy': casestudy,
        'stakeholdercategories': stakeholdercategories,
        'users': users,
        'solution_categories': solution_categories,
    }
    return render(request, 'changes/casestudy.html', context)


def user(request, user_id):
    """user view"""
    user = User.objects.get(pk=user_id)
    context = {'user': user, }
    return render(request, 'changes/user.html', context)


def userincasestudy(request, user_id, casestudy_id):
    """userincasestudy view"""
    user = UserInCasestudy.objects.get(user_id=user_id,
                                       casestudy_id=casestudy_id)
    other_casestudies = user.user.casestudies.exclude(pk=casestudy_id).all
    context = {'user': user,
               'other_casestudies': other_casestudies,
               }
    return render(request, 'changes/user_in_casestudy.html', context)

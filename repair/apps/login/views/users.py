
from django.contrib.auth.models import Group, User

from publications_bootstrap.models import Publication
from django.utils.translation import ugettext_lazy as _

from rest_framework import viewsets, mixins
from rest_framework.response import Response
from reversion.views import RevisionMixin
from django.contrib.auth import views as auth_views
from django.views import View
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
import json

from repair.apps.login.models import CaseStudy, UserInCasestudy
from repair.apps.login.serializers import (UserSerializer,
                                           GroupSerializer,
                                           CaseStudySerializer,
                                           CaseStudyListSerializer,
                                           UserInCasestudySerializer,
                                           PublicationSerializer)

from repair.apps.utils.views import (CasestudyViewSetMixin,
                                     ModelPermissionViewSet,
                                     ReadUpdatePermissionViewSet)
from django.contrib.gis.db.models.functions import PointOnSurface
from repair.apps.login.models import Profile


class UserViewSet(ModelPermissionViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(ModelPermissionViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class CaseStudyViewSet(RevisionMixin,
                       CasestudyViewSetMixin,
                       ModelPermissionViewSet):
    """
    API endpoint that allows casestudy to be viewed or edited.
    """

    queryset = CaseStudy.objects.all()
    serializer_class = CaseStudySerializer
    serializers = {'list': CaseStudyListSerializer,}

    # override list view (don't check permission, everyone can see the
    # overview of the casestudies)
    def list(self, request, **kwargs):
        queryset = CaseStudy.objects.all() if request.query_params.get('all') \
            else self.get_queryset()
        serializer = self.serializer_class(queryset, many=True,
                                           context={'request': request, })
        return Response(serializer.data)

    def get_queryset(self):
        user_id = -1 if self.request.user.id is None else self.request.user.id
        ids = []
        queryset = CaseStudy.objects.all()
        for casestudy in queryset:
            if casestudy.userincasestudy_set.all().filter(user__id=user_id):
                ids.append(casestudy.id)
        casestudies = queryset.filter(id__in=ids)
        return casestudies


class UserInCasestudyViewSet(CasestudyViewSetMixin,
                             ReadUpdatePermissionViewSet):
    """
    API endpoint that allows userincasestudy to be viewed or edited.
    """
    queryset = UserInCasestudy.objects.all()
    serializer_class = UserInCasestudySerializer


class PublicationView(ModelPermissionViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    pagination_class = None


class LoginView(auth_views.LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        session = self.request.session
        profile = Profile.objects.get(user=self.request.user)
        persist = profile.session
        if len(persist) > 0:
            for k, v in json.loads(persist).items():
                session[k] = v
        return response


class SessionView(View):
    MODES = {
        'Workshop': 0,
        'Setup': 1,
    }
    EXCLUDE_PERSIST = ['url_pks', 'csrfmiddlewaretoken', 'language']

    def persist(self):
        profile = Profile.objects.get(user=self.request.user)
        persist = self._session_dict
        profile.session = json.dumps(persist)
        profile.save()

    def post(self, request):
        if not request.user.is_authenticated:
            return HttpResponse(_('Unauthorized'), status=401)
        _next = None

        # form data
        if request.content_type in ['application/x-www-form-urlencoded',
                                    'multipart/form-data']:
            casestudy = request.POST.get('casestudy')
            mode = request.POST.get('mode')
            _next = request.POST.get('next', None)
        # json data
        elif request.content_type == 'application/json' and request.body:
            json_body = json.loads(request.body)
            casestudy = json_body.get('casestudy')
            mode = json_body.get('mode')
            for k, v in json_body.items():
                request.session[k] = v

        if casestudy is not None:
            request.session['casestudy'] = casestudy
        if mode is not None:
            try:
                mode = int(mode)
            except ValueError:
                return HttpResponseBadRequest('invalid mode')
            if mode not in self.MODES.values():
                return HttpResponseBadRequest('invalid mode')
            request.session['mode'] = mode

        self.persist()

        if (_next):
            return HttpResponseRedirect(_next)
        else:
            return self.get(request)

    @property
    def _session_dict(self):
        return {k: v for k, v in self.request.session.items()
                if not k.startswith('_') and
                k not in self.EXCLUDE_PERSIST}

    def get(self, request):
        if not request.user.is_authenticated:
            return HttpResponse(_('Unauthorized'), status=401)
        response = self._session_dict

        # sometimes (seems random) django forgets its latest session changes
        # workaround: load them from the db
        profile = Profile.objects.get(user=self.request.user)
        persist = profile.session
        if len(persist) > 0:
            for k, v in json.loads(persist).items():
                response[k] = v

        response['language'] = request.LANGUAGE_CODE
        response['mode'] = request.session.get('mode', self.MODES['Workshop'])

        return JsonResponse(response)


class PasswordChangeView(auth_views.PasswordChangeView):
    def get(self, request, *args, **kwargs):
        if not request.user.profile.can_change_password:
            return HttpResponse(_('Unauthorized'), status=401)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.profile.can_change_password:
            return HttpResponse(_('Unauthorized'), status=401)
        return super().post(request, *args, **kwargs)

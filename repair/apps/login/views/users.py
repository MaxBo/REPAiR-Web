
from django.contrib.auth.models import Group, User

from publications_bootstrap.models import Publication

from rest_framework import viewsets, mixins
from rest_framework.response import Response
from reversion.views import RevisionMixin

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

    def list(self, request, **kwargs):
        # TODO: this overwrites the list function of ModelPermissionTest
        # -> Permission is not checked!
        self.check_permission(request, 'view')
        user_id = -1 if request.user.id is None else request.user.id
        casestudies = set()
        for casestudy in self.queryset:
            if casestudy.userincasestudy_set.all().filter(user__id=user_id):
                casestudies.add(casestudy)
        serializer = self.serializer_class(casestudies, many=True,
                                           context={'request': request, })
        return Response(serializer.data)


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

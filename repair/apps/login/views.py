from abc import ABC
from django.shortcuts import render
from django.contrib.auth.models import Group, User
from rest_framework import viewsets
from rest_framework.response import Response
from repair.apps.login.models import Profile, CaseStudy, UserInCasestudy
from repair.apps.login.serializers import (UserSerializer,
                                           ProfileSerializer,
                                           GroupSerializer,
                                           CaseStudySerializer,
                                           UserInCasestudySerializer)


class OnlyCasestudyMixin(ABC):


    def list(self, request, **kwargs):
        self.set_casestudy(kwargs, request)
        lookup_args = {v:kwargs[k] for k, v
                       in self.serializer_class.parent_lookup_kwargs.items()}
        queryset = self.queryset.model.objects.filter(**lookup_args)
        serializer = self.serializer_class(queryset, many=True,
                                           context={'request': request, })
        return Response(serializer.data)

    def set_casestudy(self, kwargs, request):
        casestudy_pk = kwargs.get('casestudy_pk')
        if casestudy_pk is not None:
            request.session['casestudy'] = casestudy_pk

    def create(self, request, casestudy_pk=None, **kwargs):
        request.session['casestudy'] = casestudy_pk
        user_id = request.data.get('user', request.session.user.id) or -1
        try:
            UserInCasestudy.objects.get(user_id=request.data['user'],
                                        casestudy_id=casestudy_pk)
        except(UserInCasestudy.DoesNotExist):
            return Response({'detail': 'User does not exist in Casestudy!'},
                            status=status.HTTP_406_NOT_ACCEPTABLE)
        request.data['user'] = user_id
        return super().create(request **kwargs)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Profile.objects.all().order_by('-user__date_joined')
    serializer_class = ProfileSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class CaseStudyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows casestudy to be viewed or edited.
    """
    queryset = CaseStudy.objects.all()
    serializer_class = CaseStudySerializer

    #def retrieve(self, request, *args, **kwargs):
        #"""store the selected casestudy_id in the session as 'casestudy' """
        #request.session['casestudy'] = kwargs['pk']
        #return super().retrieve(request, *args, **kwargs)


class UserInCasestudyViewSet(OnlyCasestudyMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows userincasestudy to be viewed or edited.
    """
    queryset = UserInCasestudy.objects.all()
    serializer_class = UserInCasestudySerializer


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

from django.shortcuts import render
from django.contrib.auth.models import Group, User
from rest_framework import viewsets
from repair.apps.login.models import Profile, CaseStudy, UserInCasestudy
from repair.apps.login.serializers import (UserSerializer,
                                           ProfileSerializer,
                                           GroupSerializer,
                                           CaseStudySerializer,
                                           UserInCasestudySerializer)


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

    def retrieve(self, request, *args, **kwargs):
        """store the selected casestudy_id in the session as 'casestudy' """
        request.session['casestudy'] = kwargs['pk']
        return super().retrieve(request, *args, **kwargs)


class UserInCasestudyViewSet(viewsets.ModelViewSet):
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

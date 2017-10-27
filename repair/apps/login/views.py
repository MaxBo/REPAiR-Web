from django.contrib.auth.models import Group
from repair.apps.login.models import Profile, CaseStudy, User
from rest_framework import viewsets
from repair.apps.login.serializers import (UserSerializer,
                                           ProfileSerializer,
                                           GroupSerializer,
                                           CaseStudySerializer)


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
    queryset = Profile.objects.all()  #.order_by('-user__date_joined')
    serializer_class = ProfileSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class CaseStudyViewSet(viewsets.ModelViewSet):
    queryset = CaseStudy.objects.all()
    serializer_class = CaseStudySerializer


def casestudy(request, casestudy_id):
    casestudy = CaseStudy.objects.get(pk=casestudy_id)
    stakeholder_categories = casestudy.stakeholdercategory_set.all()
    users = casestudy.user_set.all()
    solution_categories = casestudy.solution_categories

    context = {
        'casestudy': casestudy,
        'stakeholder_categories': stakeholder_categories,
        'users': users,
        'solution_categories': solution_categories,
               }
    return render(request, 'changes/casestudy.html', context)


def user(request, user_id):
    user = User.objects.get(pk=user_id)
    context = {'user': user,
               }
    return render(request, 'changes/user.html', context)


def userincasestudy(request, user_id, casestudy_id):
    user = UserInCasestudy.objects.get(user_id=user_id,
                                       casestudy_id=casestudy_id)
    other_casestudies = user.user.casestudies.exclude(pk=casestudy_id).all
    context = {'user': user,
               'other_casestudies': other_casestudies,
               }
    return render(request, 'changes/user_in_casestudy.html', context)


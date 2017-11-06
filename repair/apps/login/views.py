from abc import ABC
from django.shortcuts import render
from django.contrib.auth.models import Group, User
from rest_framework import viewsets
from rest_framework.response import Response
from repair.apps.login.models import Profile, CaseStudy, UserInCasestudy
from repair.apps.login.serializers import (UserSerializer,
                                           GroupSerializer,
                                           CaseStudySerializer,
                                           UserInCasestudySerializer)


class MultiSerializerViewSetMixin(ABC):
    """
    use this mixin to define different serializers
    for post and put requests
    To define them in the serializer_action_classes

    serializer_action_classes = {'list': MyGetSerializer,
                                 'create': MyPostSerializer,}
    """
    serializer_action_classes = {}

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super(MultiSerializerViewSetMixin, self).\
                   get_serializer_class()


class OnlyCasestudyMixin(ABC):
    """
    This Mixin provides a list and a create method to get only
    items of the current casestudy
    """

    def set_casestudy(self, kwargs, request):
        """set the casestudy as a session attribute if its in the kwargs"""
        request.session['casestudy_pk'] = kwargs
        #casestudy_pk = kwargs.get('casestudy_pk')
        #if casestudy_pk is not None:
            #request.session['casestudy_pk'] = {'casestudy_pk': casestudy_pk}

    def list(self, request, **kwargs):
        """
        filter the queryset with the lookup-arguments
        and then render the filtered queryset with the serializer
        the lookup-arguments are defined in the "parent_lookup_kwargs" of the
        Serializer-Class
        """
        SerializerClass = self.get_serializer_class()
        self.set_casestudy(kwargs, request)
        lookup_args = {v: kwargs[k] for k, v
                       in SerializerClass.parent_lookup_kwargs.items()}
        queryset = self.queryset.model.objects.filter(**lookup_args)
        serializer = SerializerClass(queryset, many=True,
                                     context={'request': request, })
        return Response(serializer.data)


class OnlySubsetMixin(OnlyCasestudyMixin):
    """"""
    def set_casestudy(self, kwargs, request):
        """set the casestudy as a session attribute if its in the kwargs"""
        request.session['casestudy_pk'] = kwargs


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


class CaseStudyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows casestudy to be viewed or edited.
    """
    queryset = CaseStudy.objects.all()
    serializer_class = CaseStudySerializer


class UserInCasestudyViewSet(OnlyCasestudyMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows userincasestudy to be viewed or edited.
    """
    queryset = UserInCasestudy.objects.all()
    serializer_class = UserInCasestudySerializer


###############################################################################
###   views for the templates

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

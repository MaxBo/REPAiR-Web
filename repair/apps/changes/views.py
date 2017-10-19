from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.views.generic import TemplateView
from django.shortcuts import render
import django.db.models

from django.utils.translation import ugettext as _
from rest_framework import viewsets
from repair.apps.changes.models import (CaseStudy,
                                        Unit,
                                        User,
                                        UserInCasestudy,
                                        StakeholderCategory,
                                        Stakeholder,
                                        SolutionCategory,
                                        Solution,
                                        Implementation,
                                        SolutionInImplementation,
                                        Strategy,
                                        )

from repair.apps.changes.serializers import (CaseStudySerializer,
                                             StakeholderCategorySerializer,
                                             StakeholderSerializer,
                                             SolutionSerializer,
                                             SolutionCategorySerializer,
                                             UserSerializer,
                                             SolutionPostSerializer,
                                             SolutionCategoryPostSerializer,
                                             )


from repair.apps.changes.forms import NameForm



class CaseStudyViewSet(viewsets.ModelViewSet):
    queryset = CaseStudy.objects.all()
    serializer_class = CaseStudySerializer


class StakeholderCategoryViewSet(viewsets.ModelViewSet):
    queryset = StakeholderCategory.objects.all()
    serializer_class = StakeholderCategorySerializer


class StakeholderViewSet(viewsets.ModelViewSet):
    queryset = Stakeholder.objects.all()
    serializer_class = StakeholderSerializer


class SolutionCategoryViewSet(viewsets.ModelViewSet):
    queryset = SolutionCategory.objects.all()
    serializer_class = SolutionCategorySerializer


class SolutionViewSet(viewsets.ModelViewSet):
    queryset = Solution.objects.all()
    serializer_class = SolutionSerializer


def index(request):
    casestudy_list = CaseStudy.objects.order_by('id')[:20]
    users = User.objects.order_by('id')[:20]
    context = {'casestudy_list': casestudy_list,
               'users': users,}
    return render(request, 'changes/index.html', context)

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

def stakeholder_categories(request, stakeholder_category_id):
    stakeholder_category = StakeholderCategory.objects.get(
        pk=stakeholder_category_id)
    stakeholders = stakeholder_category.stakeholder_set.all()
    context = {'stakeholder_category': stakeholder_category,
               'stakeholders': stakeholders,
               }
    return render(request, 'changes/stakeholder_category.html', context)

def solutioncategories(request, solutioncategory_id):
    solution_category = SolutionCategory.objects.get(
        pk=solutioncategory_id)
    context = {'solution_category': solution_category,
               }
    return render(request, 'changes/solution_category.html', context)


def stakeholders(request, stakeholder_id):
    stakeholder = Stakeholder.objects.get(pk=stakeholder_id)
    if request.method == 'POST':
        form = NameForm(request.POST)
        if form.is_valid():
            stakeholder.name = form.cleaned_data['name']
            stakeholder.full_clean()
            stakeholder.save()
            return HttpResponseRedirect('/changes/stakeholdercategories/{}'.format(stakeholder.stakeholder_category.id))
    context = {'stakeholder': stakeholder,
               }
    return render(request, 'changes/stakeholder.html', context)

def implementations(request, implementation_id):
    implementation = Implementation.objects.get(pk=implementation_id)
    solutions = implementation.solutioninimplementation_set.all()

    context = {'implementation': implementation,
               'solutions': solutions,
               }
    return render(request, 'changes/implementation.html', context)

def solutions(request, solution_id):
    solution = Solution.objects.get(pk=solution_id)
    implementations = solution.implementation_set.all()
    print(implementations)
    context = {'solution': solution,
               }
    return render(request, 'changes/solution.html', context)

def solution_in_implematation(request, implementation_id, solution_id):
    sii = SolutionInImplementation.objects.get(
        implementation=implementation_id,
        solution=solution_id)
    geometries = sii.solutioninimplementationgeometry_set.all()
    quantities = sii.solutioninimplementationquantity_set.all()

    context = {'sii': sii,
               'geometries': geometries,
               'quantities': quantities,
               }
    return render(request, 'changes/solution_in_implementation.html', context)

def strategies(request, strategy_id):
    strategy = Strategy.objects.get(pk=strategy_id)
    implementations = strategy.implementations.all()

    context = {'strategy': strategy,
               'implementations': implementations,
               }
    return render(request, 'changes/strategy.html', context)

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


# API View
from django.http import Http404, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics

class SolutionCategoriesListApiView(generics.ListCreateAPIView):
    serializer_class = SolutionCategorySerializer

    def get_queryset(self):
        casestudy_id = self.kwargs['casestudy_id']
        casestudy = CaseStudy.objects.get(id=casestudy_id)
        return casestudy.solution_categories

    def list(self, request, casestudy_id):
        queryset = self.get_queryset()
        #queryset = queryset.filter(id=1)
        serializer = SolutionCategorySerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, casestudy_id, format=None):
        serializer = SolutionCategoryPostSerializer(data=request.data)
        try:
            UserInCasestudy.objects.get(user_id=request.data['user'],
                                        casestudy_id=casestudy_id)
        except(UserInCasestudy.DoesNotExist):
            return Response({'detail': 'User does not exist in Casestudy!'},
                            status=status.HTTP_406_NOT_ACCEPTABLE)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SolutionCategoryApiView(APIView):
    def get_object(self, casestudy_id, solution_category_id):
        try:
            casestudy = CaseStudy.objects.get(id=casestudy_id)
            solution_categories = casestudy.solution_categories
            for solution_category in solution_categories:
                if solution_category.id == int(solution_category_id):
                    return solution_category
        except Solution.DoesNotExist:
            raise Http404

    def get(self, request, casestudy_id, solution_category, format=None):
        solution_category = self.get_object(casestudy_id, solution_category)
        if solution_category:
            serializer = SolutionCategorySerializer(solution_category)
            return Response(serializer.data)
        else:
            return Response(None)


class SolutionsListApiView(generics.ListCreateAPIView):
    serializer_class = SolutionSerializer

    def get_queryset(self):
        casestudy_id = self.kwargs['casestudy_id']
        solution_category_id = self.kwargs['solution_category']
        solutions = Solution.objects.filter(
            solution_category_id=solution_category_id)
        return solutions

    def list(self, request, casestudy_id, solution_category):
        queryset = self.get_queryset()
        serializer = SolutionSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, casestudy_id, solution_category, format=None):
        data=request.data
        data['solution_category'] = solution_category  #SolutionCategory.objects.get(id=int(solution_category))
        serializer = SolutionPostSerializer(data=data)
        try:
            UserInCasestudy.objects.get(user_id=data['user'], casestudy_id=casestudy_id)
        except(UserInCasestudy.DoesNotExist):
            return Response({'detail': 'User does not exist in Casestudy!'},
                            status=status.HTTP_406_NOT_ACCEPTABLE)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SolutionApiView(APIView):
    def get_object(self, casestudy_id, solution_category_id, solution_id):
        try:
            solution = Solution.objects.get(
                solution_category_id=solution_category_id,
                id=solution_id)
            if solution.casestudy.id == int(casestudy_id):
                    return solution
        except Solution.DoesNotExist:
            raise Http404

    def get(self, request, casestudy_id, solution_category, solution_id, format=None):
        got_object = self.get_object(casestudy_id, solution_category, solution_id)
        if got_object:
            serializer = SolutionSerializer(got_object)
            return Response(serializer.data)
        else:
            return Response(None)
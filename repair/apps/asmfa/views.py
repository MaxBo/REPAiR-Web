# API View
from django.http import Http404, JsonResponse
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status, generics

from repair.apps.asmfa.models import ActivityGroup
from repair.apps.asmfa.serializers import ActivityGroupSerializer


class ActivityGroupViewSet(ViewSet):

    def list(self, request, casestudy_pk=None):
        queryset = ActivityGroup.objects.filter(case_study=casestudy_pk)
        serializer = ActivityGroupSerializer(queryset, many=True)
        return Response(serializer.data)


#class ActivityGroupApiView(APIView):
    #def get_object(self, casestudy_id, solution_category_id):
        #try:
            #casestudy = CaseStudy.objects.get(id=casestudy_id)
            #solution_categories = casestudy.solution_categories
            #for solution_category in solution_categories:
                #if solution_category.id == int(solution_category_id):
                    #return solution_category
        #except Solution.DoesNotExist:
            #raise Http404

    #def get(self, request, casestudy_id, solution_category, format=None):
        #solution_category = self.get_object(casestudy_id, solution_category)
        #if solution_category:
            #serializer = SolutionCategorySerializer(solution_category)
            #return Response(serializer.data)
        #else:
            #return Response(None)

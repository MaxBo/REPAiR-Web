from rest_framework import viewsets, exceptions
from django.views import View
from publications_bootstrap.models import Publication
from repair.apps.login.serializers import PublicationSerializer
from django.http import HttpResponseRedirect, JsonResponse



class ModelPermissionViewSet(viewsets.ModelViewSet):
    """
    check permissions
    """
    add_perm = None
    change_perm = None
    delete_perm = None

    def create(self, request, **kwargs):
        if self.add_perm:
            if not request.user.has_perm(self.add_perm):
                raise exceptions.PermissionDenied()
        return super().create(request, **kwargs)

    def destroy(self, request, **kwargs):
        if self.add_perm:
            if not request.user.has_perm(self.delete_perm):
                raise exceptions.PermissionDenied()
        return super().destroy(request, **kwargs)


class SessionView(View):
    def post(self, request):
        if request.POST['casestudy']:
            request.session['casestudy'] = request.POST['casestudy']
            next = request.POST.get('next', '/')
            return HttpResponseRedirect(next)

    def get(self, request):
        response =  {'casestudy': request.session.get('casestudy')}
        return JsonResponse(response)


class PublicationView(ModelPermissionViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    pagination_class = None
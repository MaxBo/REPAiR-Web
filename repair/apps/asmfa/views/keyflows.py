# API View
from reversion.views import RevisionMixin
from django.db.models import Q
from rest_framework import serializers, exceptions
from rest_framework_datatables import pagination
from django.utils.translation import ugettext_lazy as _
from django_filters.rest_framework import (
    DjangoFilterBackend, Filter, FilterSet, MultipleChoiceFilter)

from repair.apps.asmfa.models import (
    Keyflow,
    KeyflowInCasestudy,
    Product,
    Material,
    Waste, 
)

from repair.apps.asmfa.serializers import (
    KeyflowSerializer,
    KeyflowInCasestudySerializer,
    KeyflowInCasestudyPostSerializer,
    ProductSerializer,
    MaterialSerializer,
    MaterialListSerializer,
    AllMaterialSerializer,
    AllMaterialListSerializer,
    WasteSerializer
)

from repair.apps.login.views import CasestudyViewSetMixin
from repair.apps.utils.views import ModelPermissionViewSet


class UnlimitedResultsSetPagination(pagination.DatatablesPageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'


class KeyflowViewSet(ModelPermissionViewSet):
    add_perm = 'asmfa.add_keyflow'
    change_perm = 'asmfa.change_keyflow'
    delete_perm = 'asmfa.delete_keyflow'
    queryset = Keyflow.objects.all()
    serializer_class = KeyflowSerializer


class KeyflowInCasestudyViewSet(CasestudyViewSetMixin, ModelPermissionViewSet):
    """
    API endpoint that allows Keyflowincasestudy to be viewed or edited.
    """
    add_perm = 'asmfa.add_keyflowincasestudy'
    change_perm = 'asmfa.change_keyflowincasestudy'
    delete_perm = 'asmfa.delete_keyflowincasestudy'
    queryset = KeyflowInCasestudy.objects.all()
    serializer_class = KeyflowInCasestudySerializer
    serializers = {'create': KeyflowInCasestudyPostSerializer,
                   'update': KeyflowInCasestudyPostSerializer, }


class CommaSeparatedValueFilter(Filter):
    def filter(self, qs, value):
        if not value:
            return qs
        self.lookup_expr = 'in'
        values = value.split(',')
        return super(CommaSeparatedValueFilter, self).filter(qs, values)


class ProductFilter(FilterSet):
    nace = CommaSeparatedValueFilter(name='nace')

    class Meta:
        model = Product
        fields = ('nace', 'cpa')


class WasteFilter(FilterSet):
    nace = CommaSeparatedValueFilter(name='nace')

    class Meta:
        model = Waste
        fields = ('nace', 'hazardous', 'wastetype', 'ewc')


class MaterialFilter(FilterSet):

    class Meta:
        model = Material
        fields = ('parent', 'keyflow')


class ProductViewSet(RevisionMixin, ModelPermissionViewSet):
    pagination_class = UnlimitedResultsSetPagination
    add_perm = 'asmfa.add_product'
    change_perm = 'asmfa.change_product'
    delete_perm = 'asmfa.delete_product'
    queryset = Product.objects.order_by('id')
    serializer_class = ProductSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = ProductFilter
    
    # DjangoFilterBackend is not able to parse query params in array form
    # (e.g. ?nace[]=xxx&nace[]=yyy)
    def list(self, request, **kwargs):
        if 'nace[]' in request.query_params.keys():
            nace = request.GET.getlist('nace[]')
            self.queryset = self.queryset.filter(nace__in=nace)
        return super().list(request, **kwargs)


class WasteViewSet(RevisionMixin, ModelPermissionViewSet):
    pagination_class = UnlimitedResultsSetPagination
    add_perm = 'asmfa.add_waste'
    change_perm = 'asmfa.change_waste'
    delete_perm = 'asmfa.delete_waste'
    queryset = Waste.objects.order_by('id')
    serializer_class = WasteSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = WasteFilter
    
    # DjangoFilterBackend is not able to parse query params in array form
    # (e.g. ?nace[]=xxx&nace[]=yyy)
    def list(self, request, **kwargs):
        if 'nace[]' in request.query_params.keys():
            nace = request.GET.getlist('nace[]')
            self.queryset = self.queryset.filter(nace__in=nace)
        return super().list(request, **kwargs)


class AllMaterialViewSet(RevisionMixin, ModelPermissionViewSet):
    pagination_class = None
    add_perm = 'asmfa.add_material'
    change_perm = 'asmfa.change_material'
    delete_perm = 'asmfa.delete_material'
    queryset = Material.objects.order_by('id')
    serializer_class = AllMaterialSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = MaterialFilter
    serializers = {'list': AllMaterialListSerializer}

class MaterialViewSet(CasestudyViewSetMixin, AllMaterialViewSet):
    serializer_class = MaterialSerializer
    serializers = {'list': MaterialListSerializer}
    
    # include materials with keyflows with pk null as well (those are the default ones)
    def get_queryset(self):
        model = self.serializer_class.Meta.model
        keyflow_id = self.kwargs['keyflow_pk']
        return model.objects\
               .filter(Q(keyflow__isnull=True) | Q(keyflow=keyflow_id))\
               .order_by('id')
    
    def checkMethod(self, request, **kwargs):
        model = self.serializer_class.Meta.model
        instance = model.objects.get(id=kwargs['pk'])
        if instance.keyflow is None:
            raise exceptions.MethodNotAllowed(
                'PUT',
                _('This material is a default material '
                  'and can neither be edited nor deleted.')
            )

    def update(self, request, **kwargs):
        self.checkMethod(request, **kwargs)
        return super().update(request, **kwargs)

    def destroy(self, request, **kwargs):
        self.checkMethod(request, **kwargs)
        return super().destroy(request, **kwargs)

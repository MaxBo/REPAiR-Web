# API View
from reversion.views import RevisionMixin
from rest_framework import serializers
from rest_framework_datatables import pagination
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
        fields = ('parent', )


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


class MaterialViewSet(RevisionMixin, CasestudyViewSetMixin,
                      ModelPermissionViewSet):
    add_perm = 'asmfa.add_material'
    change_perm = 'asmfa.change_material'
    delete_perm = 'asmfa.delete_material'
    queryset = Material.objects.order_by('id')
    serializer_class = MaterialSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = MaterialFilter
    serializers = {'list': MaterialListSerializer}

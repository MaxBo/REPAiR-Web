# API View
from reversion.views import RevisionMixin
from rest_framework import serializers, pagination
from django_filters.rest_framework import DjangoFilterBackend

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
    WasteSerializer
)

from repair.apps.login.views import CasestudyViewSetMixin
from repair.apps.utils.views import ModelPermissionViewSet


class UnlimitedResultsSetPagination(pagination.PageNumberPagination):
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


class ProductViewSet(RevisionMixin, ModelPermissionViewSet):
    pagination_class = UnlimitedResultsSetPagination
    add_perm = 'asmfa.add_product'
    change_perm = 'asmfa.change_product'
    delete_perm = 'asmfa.delete_product'
    queryset = Product.objects.order_by('id')
    serializer_class = ProductSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('nace', 'cpa')


class WasteViewSet(RevisionMixin, ModelPermissionViewSet):
    pagination_class = UnlimitedResultsSetPagination
    add_perm = 'asmfa.add_waste'
    change_perm = 'asmfa.change_waste'
    delete_perm = 'asmfa.delete_waste'
    queryset = Waste.objects.order_by('id')
    serializer_class = WasteSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('nace', 'hazardous', 'wastetype', 'ewc')


class MaterialViewSet(RevisionMixin, CasestudyViewSetMixin,
                      ModelPermissionViewSet):
    add_perm = 'asmfa.add_material'
    change_perm = 'asmfa.change_material'
    delete_perm = 'asmfa.delete_material'
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer

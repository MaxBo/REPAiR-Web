# API View
from collections import OrderedDict
from itertools import chain
from abc import ABC

from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ViewSet, ModelViewSet
from rest_framework.response import Response
from rest_framework import status

from repair.apps.asmfa.models import (
    ActivityGroup,
    Activity,
    Actor,
    Flow,
    Activity2Activity,
    Actor2Actor,
    Group2Group,
    Material,
    Quality,
    MaterialInCasestudy,
    GroupStock,
    ActivityStock,
    ActorStock)

from repair.apps.asmfa.serializers import (
    ActivityGroupSerializer,
    ActivitySerializer,
    ActorSerializer,
    FlowSerializer,
    Actor2ActorSerializer,
    Activity2ActivitySerializer,
    Group2GroupSerializer,
    ActorListSerializer,
    MaterialSerializer,
    QualitySerializer,
    MaterialInCasestudySerializer,
    GroupStockSerializer,
    ActivityStockSerializer,
    ActorStockSerializer,
    AllActivitySerializer,
    AllActorSerializer)

from repair.apps.login.views import OnlyCasestudyMixin, OnlySubsetMixin


class ActivityGroupViewSet(OnlyCasestudyMixin, ModelViewSet):
    serializer_class = ActivityGroupSerializer
    queryset = ActivityGroup.objects.all()


class ActivityViewSet(OnlyCasestudyMixin, ModelViewSet):
    serializer_class = ActivitySerializer
    queryset = Activity.objects.all()


class ActorViewSet(OnlyCasestudyMixin, ModelViewSet):
    serializer_class = ActorSerializer
    queryset = Actor.objects.all()


class AllActivityViewSet(ActivityViewSet):
    serializer_class = AllActivitySerializer


class AllActorViewSet(ActorViewSet):
    serializer_class = AllActorSerializer


class MaterialViewSet(ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer


class QualityViewSet(ModelViewSet):
    queryset = Quality.objects.all()
    serializer_class = QualitySerializer


class MaterialInCasestudyViewSet(OnlyCasestudyMixin, ModelViewSet):
    """
    API endpoint that allows materialincasestudy to be viewed or edited.
    """
    queryset = MaterialInCasestudy.objects.all()
    serializer_class = MaterialInCasestudySerializer


class GroupStockViewSet(OnlySubsetMixin, ModelViewSet):
    queryset = GroupStock.objects.all()
    serializer_class = GroupStockSerializer


class ActivityStockViewSet(OnlySubsetMixin, ModelViewSet):
    queryset = ActivityStock.objects.all()
    serializer_class = ActivityStockSerializer


class ActorStockViewSet(OnlySubsetMixin, ModelViewSet):
    queryset = ActorStock.objects.all()
    serializer_class = ActorStockSerializer



class FlowViewSet(OnlySubsetMixin, ModelViewSet, ABC):
    """
    Abstract BaseClass for a FlowViewSet
    The Subclass has to provide a model inheriting from Flow
    and a serializer-class inheriting form and a model
    """
    serializer_class = FlowSerializer
    model = Flow


class Group2GroupViewSet(FlowViewSet):
    queryset = Group2Group.objects.all()
    serializer_class = Group2GroupSerializer


class Activity2ActivityViewSet(FlowViewSet):
    queryset = Activity2Activity.objects.all()
    serializer_class = Activity2ActivitySerializer


class Actor2ActorViewSet(FlowViewSet):
    queryset = Actor2Actor.objects.all()
    serializer_class = Actor2ActorSerializer

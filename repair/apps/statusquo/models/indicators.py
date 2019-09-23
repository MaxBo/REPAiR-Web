from django.db import models
from django.core.validators import validate_comma_separated_integer_list
from enum import Enum
from enumfields import EnumIntegerField
import importlib

from repair.apps.login.models import GDSEModel
from repair.apps.asmfa.models import Material, KeyflowInCasestudy


class TriState(Enum):
    BOTH = 1
    NO = 2
    YES = 3


class SpatialChoice(Enum):
    BOTH = 1
    ORIGIN = 2
    DESTINATION = 3


class NodeLevel(Enum):
    ACTOR = 1
    ACTIVITY = 2
    ACTIVITYGROUP = 3


class IndicatorType(Enum):
    IndicatorA = 1
    IndicatorAB = 2
    IndicatorInhabitants = 3
    IndicatorArea = 4


class FlowType(Enum):
    BOTH = 1
    WASTE = 2
    PRODUCT = 3


class SpatialType(Enum):
    REGION = 1
    FOCUSAREA = 2


class IndicatorFlow(GDSEModel):
    origin_node_level = EnumIntegerField(
        enum=NodeLevel, default=NodeLevel.ACTOR)
    origin_node_ids = models.TextField(
        validators=[validate_comma_separated_integer_list],
        blank=True, null=True)
    destination_node_level = EnumIntegerField(
        enum=NodeLevel, default=NodeLevel.ACTOR)
    destination_node_ids = models.TextField(
        validators=[validate_comma_separated_integer_list],
        blank=True, null=True)
    materials = models.ManyToManyField(Material, blank=True)
    process_ids = models.TextField(
        validators=[validate_comma_separated_integer_list],
        blank=True, null=True)
    hazardous = EnumIntegerField(
        enum=TriState, default=TriState.BOTH)
    avoidable = EnumIntegerField(
        enum=TriState, default=TriState.BOTH)

    spatial_application = EnumIntegerField(
        enum=SpatialChoice, default=SpatialChoice.BOTH)

    flow_type = EnumIntegerField(
        enum=FlowType, default=FlowType.BOTH)


class FlowIndicator(GDSEModel):

    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    indicator_type = EnumIntegerField(
        enum=IndicatorType, default=IndicatorType.IndicatorA)

    flow_a = models.ForeignKey(IndicatorFlow,
                               on_delete=models.SET_NULL,
                               related_name='flow_a',
                               null=True)
    flow_b = models.ForeignKey(IndicatorFlow,
                               on_delete=models.SET_NULL,
                               related_name='flow_b',
                               null=True)

    keyflow = models.ForeignKey(KeyflowInCasestudy,
                                on_delete=models.CASCADE)

    spatial_reference = EnumIntegerField(
        enum=SpatialType, default=SpatialType.REGION)
    included = models.BooleanField(default=True)

    def get_type(self):
        module = importlib.import_module(
            'repair.apps.statusquo.views.computation')
        return getattr(module, self.indicator_type.name)

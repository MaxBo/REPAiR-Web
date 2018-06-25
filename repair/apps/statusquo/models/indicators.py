from django.db import models
from django.core.validators import validate_comma_separated_integer_list
from enum import Enum
from enumfields import EnumIntegerField

from repair.apps.login.models import GDSEModel
from repair.apps.asmfa.models import Material, KeyflowInCasestudy


class SpatialChoice(Enum):
    NONE = 0
    ORIGIN = 1
    DESTINATION = 2
    BOTH = 3


class NodeLevel(Enum):
    ACTOR = 0
    ACTIVITY = 1
    ACTIVITYGROUP = 2


class IndicatorType(Enum):
    A = 0
    AB = 1


class FlowType(Enum):
    BOTH = 0
    WASTE = 1
    PRODUCT = 2



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

    spatial_application = EnumIntegerField(
        enum=SpatialChoice, default=SpatialChoice.NONE)
    
    flow_type = EnumIntegerField(
        enum=FlowType, default=FlowType.BOTH)


class FlowIndicator(GDSEModel):
    
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    indicator_type = EnumIntegerField(
        enum=IndicatorType, default=IndicatorType.A)

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
    
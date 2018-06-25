from django.db import models
from django.core.validators import validate_comma_separated_integer_list

from repair.apps.login.models import GDSEModel
from repair.apps.asmfa.models import Material, KeyflowInCasestudy

NONE = 0
ORIGIN = 1
DESTINATION = 2
BOTH = 3

SPATIAL_CHOICES = (
    (NONE, 'none'), 
    (ORIGIN, 'origin'),
    (DESTINATION, 'destination'),
    (BOTH, 'both')
)

ACTOR_LEVEL = 0
ACTIVITY_LEVEL = 1
ACTIVITYGROUP_LEVEL = 2

NODE_LEVEL_CHOICES = (
    (ACTOR_LEVEL, 'actor'),
    (ACTIVITY_LEVEL, 'activity'),
    (ACTIVITYGROUP_LEVEL, 'activitygroup')
)

INDICATOR_TYPE_A = 0
INDICATOR_TYPE_AB = 1

INDICATOR_TYPE_CHOICES = (
    (INDICATOR_TYPE_A, 'a'),
    (INDICATOR_TYPE_AB, 'a/b')
)

FLOW_TYPE_BOTH = 0
FLOW_TYPE_WASTE = 1
FLOW_TYPE_PRODUCT = 2

FLOW_TYPE_CHOICES = (
    (FLOW_TYPE_BOTH, 'both'),
    (FLOW_TYPE_WASTE, 'waste'),
    (FLOW_TYPE_PRODUCT, 'product')
)


class IndicatorFlow(GDSEModel):
    origin_node_level = models.IntegerField(choices=NODE_LEVEL_CHOICES,
                                            default=ACTOR_LEVEL)
    origin_node_ids = models.TextField(
        validators=[validate_comma_separated_integer_list],
        blank=True, null=True)
    destination_node_level = models.IntegerField(choices=NODE_LEVEL_CHOICES,
                                                 default=ACTOR_LEVEL)
    destination_node_ids = models.TextField(
        validators=[validate_comma_separated_integer_list],
        blank=True, null=True)
    materials = models.ManyToManyField(Material, blank=True)

    spatial_application = models.IntegerField(choices=SPATIAL_CHOICES,
                                              default=NONE)
    
    flow_type = models.IntegerField(choices=FLOW_TYPE_CHOICES,
                                    default=FLOW_TYPE_BOTH)


class FlowIndicator(GDSEModel):
    
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    indicator_type = models.IntegerField(choices=INDICATOR_TYPE_CHOICES,
                                         default=INDICATOR_TYPE_A)

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
    
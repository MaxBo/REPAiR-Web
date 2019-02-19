from django.db import models
from django.core.validators import validate_comma_separated_integer_list
from enum import Enum
from enumfields import EnumIntegerField

from repair.apps.login.models import GDSEModel
from repair.apps.asmfa.models import Material, KeyflowInCasestudy
from repair.apps.statusquo.models.indicators import NodeLevel, FlowType
from repair.apps.studyarea.models import Area, AdminLevels


class Direction(Enum):
    BOTH = 1
    FROM = 2
    TO = 3


class TriState(Enum):
    BOTH = 1
    NO = 2
    YES = 3


class FlowFilter(GDSEModel):
    '''
    predefined filters for rendering flows in workshop mode
    '''
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    keyflow = models.ForeignKey(KeyflowInCasestudy, on_delete=models.CASCADE)
    filter_level = EnumIntegerField(
        enum=NodeLevel, default=NodeLevel.ACTIVITYGROUP)
    node_ids = models.TextField(
        validators=[validate_comma_separated_integer_list],
        blank=True, null=True)
    material = models.ForeignKey(Material,
                                 on_delete=models.SET_NULL,
                                 null=True)
    direction = EnumIntegerField(
        enum=Direction, default=Direction.BOTH)
    flow_type = EnumIntegerField(
        enum=FlowType, default=FlowType.BOTH)
    #hazardous = EnumIntegerField(
        #enum=TriState, default=TriState.BOTH)
    #avoidable = EnumIntegerField(
        #enum=TriState, default=TriState.BOTH)
    aggregate_materials = models.BooleanField(default=True)
    area_level = models.ForeignKey(AdminLevels,
                                   on_delete=models.SET_NULL,
                                   null=True)
    areas = models.ManyToManyField(Area, blank=True)
    included = models.BooleanField(default=True)


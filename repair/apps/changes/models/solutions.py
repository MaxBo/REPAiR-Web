
from django.contrib.gis.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
import re
import json
from enumfields import EnumIntegerField
from django.contrib.gis.geos import Polygon

from enumfields import EnumIntegerField
from enum import Enum

from repair.apps.login.models import (GDSEUniqueNameModel,
                                      GDSEModel)
from repair.apps.asmfa.models import (Activity, KeyflowInCasestudy,
                                      Material, Process)
from repair.apps.statusquo.models import SpatialChoice
from repair.apps.utils.protect_cascade import PROTECT_CASCADE

comma_separated_float_list_re = re.compile('^([-+]?\d*\.?\d+[,\s]*)+$')
double_list_validator = RegexValidator(
    comma_separated_float_list_re,
    _(u'Enter only floats separated by commas.'), 'invalid')


class Scheme(Enum):
    MODIFICATION = 0
    NEW = 1
    SHIFTORIGIN = 2
    SHIFTDESTINATION = 3
    PREPEND = 4
    APPEND = 5


class SolutionCategory(GDSEModel):
    name = models.TextField()
    keyflow = models.ForeignKey(KeyflowInCasestudy,
                                on_delete=models.CASCADE)


class Solution(GDSEModel):
    '''
    definition of a solution to be implemented by user, may affect multiple
    flows as defined in its solution-parts
    '''
    solution_category = models.ForeignKey(SolutionCategory,
                                          on_delete=PROTECT_CASCADE)
    name = models.TextField()
    description = models.TextField(default='')
    documentation = models.TextField(default='')
    currentstate_image = models.ImageField(upload_to='charts', null=True,
                                           blank=True)
    effect_image = models.ImageField(upload_to='charts', null=True,
                                     blank=True)
    activities_image = models.ImageField(upload_to='charts', null=True,
                                         blank=True)


class ImplementationQuestion(GDSEModel):
    '''
    question asked to user to determine value for calc. solution-part formula
    '''
    question = models.TextField(default='')
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE,
                                 related_name='question')
    unit = models.CharField(blank=True, default='', max_length=100)
    select_values = models.TextField(
        blank=True, validators=[double_list_validator])
    step = models.FloatField(null=True)
    min_value = models.FloatField(default=0)
    max_value = models.FloatField(default=1)
    # value is absolute or relative (defining fraction)
    is_absolute = models.BooleanField(default=False)


class PossibleImplementationArea(GDSEModel):
    '''
    possible implementation with question asked to user
    '''
    geom = models.MultiPolygonField(srid=4326)
    question = models.TextField(default='')
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE,
                                 related_name='possible_implementation_area')

    @property
    def edit_mask(self):
        if not self.geom:
            return
        bbox = Polygon([[-180, 90], [180, 90],
                        [180, -90], [-180, -90], [-180, 90]])
        mask = bbox.difference(self.geom)
        return json.loads(mask.geojson)


class FlowReference(GDSEModel):
    origin_activity = models.ForeignKey(
        Activity, on_delete=PROTECT_CASCADE,
        related_name='reference_origin', null=True)
    destination_activity = models.ForeignKey(
        Activity, on_delete=PROTECT_CASCADE,
        related_name='reference_destination', null=True)
    material = models.ForeignKey(
        Material, on_delete=PROTECT_CASCADE, null=True)
    process = models.ForeignKey(
        Process, on_delete=PROTECT_CASCADE, null=True)
    origin_area = models.ForeignKey(
        PossibleImplementationArea, on_delete=PROTECT_CASCADE,
        related_name='possible_origin_area', null=True)
    destination_area = models.ForeignKey(
        PossibleImplementationArea, on_delete=PROTECT_CASCADE,
        related_name='possible_destination_area', null=True)


class SolutionPart(GDSEModel):
    '''
    part of the solution definition, change a single implementation flow (or
    create new one by deriving it from existing)
    '''
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE,
                                 related_name='solution_parts')
    name = models.TextField()
    documentation = models.TextField(default='')

    # scheme determines how to interpret the following attributes and how
    # to apply values to graph/existing flows
    scheme = EnumIntegerField(enum=Scheme, default=Scheme.MODIFICATION)

    # implementation flows a.k.a. reference flows
    # starting point of calculation, flow changes are referenced to the flows
    # filtered by these attributes
    flow_reference = models.ForeignKey(
        FlowReference, on_delete=PROTECT_CASCADE, null=True,
        related_name='reference_solution_part')
    # changes made to reference flows
    flow_changes = models.ForeignKey(
        FlowReference, on_delete=PROTECT_CASCADE, null=True,
        related_name='reference_flow_change')

    # order of calculation, lowest first
    priority = models.IntegerField(default=0)
    ### attributes that determine the new value of the flow ###

    # question for user inputs for the formula changing the implementation flow
    # (null when no question is asked)
    question = models.ForeignKey(ImplementationQuestion, null=True,
                                 on_delete=PROTECT_CASCADE)


    # only of interest if there is no question (question is null)
    # is overriden by question.is_absolute
    is_absolute = models.BooleanField(default=False)

    # general parameters for formula
    a = models.FloatField()
    b = models.FloatField()

    def delete(self):
        if self.flow_reference:
            self.flow_reference.delete()
        if self.flow_changes:
            self.flow_reference.delete()
        super().delete()


class AffectedFlow(GDSEModel):
    '''
    flow affected by solution-part on activity level
    '''
    solution_part = models.ForeignKey(
        SolutionPart, related_name='affected_flows', on_delete=models.CASCADE)

    origin_activity = models.ForeignKey(
        Activity, on_delete=PROTECT_CASCADE, related_name='affected_origins')
    destination_activity = models.ForeignKey(
        Activity, on_delete=PROTECT_CASCADE,
        related_name='affected_destinations')
    material = models.ForeignKey(
        Material, on_delete=PROTECT_CASCADE, related_name='affected_materials')
    process = models.ForeignKey(
        Process, on_delete=PROTECT_CASCADE, related_name='affected_processes',
        null=True)


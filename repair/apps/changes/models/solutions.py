
from django.contrib.gis.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
import re
import json
from enumfields import EnumIntegerField
from django.contrib.gis.geos import Polygon

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
    question asked to user to determine value for calc. solution-part formula
    '''
    geom = models.MultiPolygonField(null=True, srid=4326, blank=True)
    name = models.TextField(default='')
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


class SolutionPart(GDSEModel):
    '''
    part of the solution definition, change a single implementation flow (or
    create new one by deriving it from existing)
    '''
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE,
                                 related_name='solution_parts')
    name = models.TextField()
    documentation = models.TextField(default='')
    implements_new_flow = models.BooleanField(default=False)
    possible_implementation_area = models.ForeignKey(
        PossibleImplementationArea, on_delete=PROTECT_CASCADE, null=True)

    # starting point of calculation (possible new flow is derived from it)
    # on activity level (only when references_part == False)
    implementation_flow_origin_activity = models.ForeignKey(
        Activity, on_delete=PROTECT_CASCADE,
        related_name='implementation_origin', null=True)
    implementation_flow_destination_activity = models.ForeignKey(
        Activity, on_delete=PROTECT_CASCADE,
        related_name='implementation_destination', null=True)
    implementation_flow_material = models.ForeignKey(
        Material, on_delete=PROTECT_CASCADE,
        related_name='implementation_material', null=True)
    implementation_flow_process = models.ForeignKey(
        Process, on_delete=PROTECT_CASCADE,
        related_name='implementation_process', null=True)

    # alternative: derive from another solution part that implements a new flow
    # (references_part == True)
    implementation_flow_solution_part = models.ForeignKey(
        "SolutionPart", on_delete=PROTECT_CASCADE,
        related_name='implementation_part', null=True)

    # where is solution part applied (origin, destination or both)
    implementation_flow_spatial_application = EnumIntegerField(
        enum=SpatialChoice, default=SpatialChoice.BOTH)

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

    # material changes (null if stays same)
    new_material = models.ForeignKey(Material, null=True,
                                     on_delete=PROTECT_CASCADE)

    # order of calculation, lowest first
    priority = models.IntegerField(default=0)

    ### fields only of interest for new flow (implements_new_flow == True) ###

    # origin is kept the same (True) -> new destination
    # destination is kept the same (False) -> new origin
    keep_origin = models.BooleanField(default=True)
    # new origin resp. destination (depending on keep_origin)
    # should not be null when implementing new flow
    new_target_activity = models.ForeignKey(
        Activity, on_delete=PROTECT_CASCADE,
        related_name='new_target', null=True)
    # text telling user what to pick on map (actor from new_target_activity)
    map_request = models.TextField(default='')


class AffectedFlow(GDSEModel):
    '''
    flow affected by solution-part on activity level
    '''
    solution_part = models.ForeignKey(
        SolutionPart, related_name='affected_flow', on_delete=models.CASCADE)

    origin_activity = models.ForeignKey(
        Activity, on_delete=PROTECT_CASCADE, related_name='affected_origin')
    destination_activity = models.ForeignKey(
        Activity, on_delete=PROTECT_CASCADE,
        related_name='affected_destination')
    material = models.ForeignKey(
        Material, on_delete=PROTECT_CASCADE, related_name='affected_material')
    process = models.ForeignKey(
        Process, on_delete=PROTECT_CASCADE, related_name='affected_process',
        null=True)


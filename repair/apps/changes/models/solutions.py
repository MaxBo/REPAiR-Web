
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
    possible_implementation_area = models.MultiPolygonField(
        null=True, srid=4326, blank=True)

    @property
    def edit_mask(self):
        if not self.possible_implementation_area:
            return
        bbox = Polygon([[-180, 90], [180, 90],
                        [180, -90], [-180, -90], [-180, 90]])
        mask = bbox.difference(self.possible_implementation_area)
        return json.loads(mask.geojson)


class ImplementationQuestion(GDSEModel):
    '''
    question asked to user to determine value for calc. solution-part formula
    '''
    question = models.TextField(default='')
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE,
                                 related_name='question')
    unit = models.CharField(blank=True, default='', max_length=100)
    select_values = models.TextField(blank=True, validators=[double_list_validator])
    step = models.FloatField(null=True)
    min_value = models.FloatField(default=0)
    max_value = models.FloatField(default=1)
    # value is absolute or relative (defining fraction)
    is_absolute = models.BooleanField(default=False)


# TODO: ImplementationQuantity is missing


class SolutionPart(GDSEModel):
    '''
    part of the solution definition, change a single implementation flow (or
    create new one by deriving it from existing)
    '''
    solution = models.ForeignKey(Solution, on_delete=models.CASCADE,
                                 related_name='solution_part')
    name = models.TextField()
    documentation = models.TextField(default='')
    implements_new_flow = models.BooleanField(default=False)

    # starting point of calculation (possible new flow is derived from it)
    # on activity level
    implementation_flow_origin_activity = models.ForeignKey(
        Activity, on_delete=PROTECT_CASCADE,
        related_name='implementation_origin')
    implementation_flow_destination_activity = models.ForeignKey(
        Activity, on_delete=PROTECT_CASCADE,
        related_name='implementation_destination', null=True)
    implementation_flow_material = models.ForeignKey(
        Material, on_delete=PROTECT_CASCADE,
        related_name='implementation_material')
    implementation_flow_process = models.ForeignKey(
        Process, on_delete=PROTECT_CASCADE,
        related_name='implementation_process', null=True)
    implementation_flow_spatial_application = EnumIntegerField(
        enum=SpatialChoice, default=SpatialChoice.BOTH)

    # parameters for formula changing the implementation flow
    question = models.ForeignKey(ImplementationQuestion, null=True,
                                 on_delete=PROTECT_CASCADE)
    a = models.FloatField()
    b = models.FloatField()

    # fields only of interest for new flow
    keep_origin = models.BooleanField(default=True)  # if False: keep dest.
    # new origin resp. activity (depending on keep_origin)
    new_target_activity = models.ForeignKey(
        Activity, on_delete=PROTECT_CASCADE,
        related_name='new_target', null=True)
    map_request = models.TextField(default='') # tells user what to pick on map

    # order of calculation, lowest first
    priority = models.IntegerField(default=0)

    # overriden by question, only of interest if there is no question
    is_absolute = models.BooleanField(default=False)


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


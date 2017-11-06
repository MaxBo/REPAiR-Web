from django.test import TestCase
from django.core.validators import ValidationError


from repair.apps.asmfa.models import (
    Activity,
    Activity2Activity,
    ActivityGroup,
    ActivityStock,
    Actor,
    Actor2Actor,
    ActorStock,
    DataEntry,
    Flow,
    Geolocation,
    Group2Group,
    GroupStock,
    Node,
    Stock,
    )

from repair.apps.login.models import CaseStudy


class ModelTest(TestCase):

    #fixtures = ['user_fixture.json',
                #'activities_dummy_data.json',]

    def test_string_representation(self):
        for Model in (
            Activity,
            Activity2Activity,
            ActivityGroup,
            ActivityStock,
            Actor,
            Actor2Actor,
            ActorStock,
            DataEntry,
            Geolocation,
            Group2Group,
            GroupStock,
            ):

            print('{} has {} test data entries'.format(
                Model, Model.objects.count()))

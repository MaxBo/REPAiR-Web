from django.test import TestCase
from django.core.validators import ValidationError

from .models import CaseStudy, User, UserInCasestudy
from .factories import *


class ModelTest(TestCase):

    fixtures = ['login_fixture.json']

    def test_string_representation(self):
        for Model in (CaseStudy,
                     User,
                     ):

            model = Model(name="MyName")
            self.assertEqual(str(model),"MyName")

from django.test import TestCase
from django.core.validators import ValidationError

from repair.apps.login.models import CaseStudy, User, GDSEUser
from repair.apps.login.factories import *


class ModelTest(TestCase):

    #fixtures = ['login_fixture.json']


    def test_2(self):
        user = GDSEUserFactory()
        print(user)

    #def test_string_representation(self):
        #for Model in (CaseStudy,
                     #User,
                     #):

            #model = Model(name="MyName")
            #self.assertEqual(str(model),"MyName")

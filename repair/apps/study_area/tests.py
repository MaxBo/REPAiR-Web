from django.test import TestCase
from repair.apps.study_area.models import Nodes, Links

class TestTestCase(TestCase):


    def test_lol_equals_lol(self):
        self.assertEqual("lol", "lol")

    def test_one_smaller_5(self):
        self.assertGreaterEqual(5, 1)
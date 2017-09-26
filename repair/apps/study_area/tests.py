from django.test import TestCase
from repair.apps.study_area.models import Nodes, Links

class TestTestCase(TestCase):


    def test_lol_equals_lol(self):
        self.assertEqual("lol", "lol")

    def test_one_smaller_5(self):
        self.assertGreaterEqual(5, 1)

class TestModels(TestCase):

    def test_save_node(self):
        n1 = Nodes(node_id=0, location='Germany', x_coord=4.5, y_coord=8.3)
        n1.save()
        self.assertEqual(n1.location, 'Germany')

from django.test import TestCase

class TestTestCase(TestCase):


    def test_lol_equals_lol(self):
        self.assertEqual("lol", "lol")

    def test_one_smaller_5(self):
        self.assertGreaterEqual(5, 1)
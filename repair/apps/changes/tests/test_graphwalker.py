from django.test import TestCase
from repair.apps.changes.models import Solution

class GraphWalkerTests(TestCase):
    """
    Testclass for the graph walker

    loads the data for the peel pioneer example from a fixture
    """

    fixtures = ['peelpioneer_data']

    def test_solution_logic(self):
        solution = Solution.objects.all()
        print(solution)
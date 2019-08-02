from django.test import TestCase
from repair.apps.asmfa.models import Actor
from repair.apps.changes.models import Solution, Strategy
from repair.apps.asmfa.graphs.graph import StrategyGraph

class GraphWalkerTests(TestCase):
    """
    Testclass for the graph walker

    loads the data for the peel pioneer example from a fixture
    """

    fixtures = ['peelpioneer_data']

    def test_solution_logic(self):
        solution = Solution.objects.all()
        print(solution)

    def test_select_closest_actor(self):
        actors_in_solution = Actor.objects.filter(activity__id__lte=1845)
        possible_target_actors = Actor.objects.filter(activity__id__gte=1846)
        target_actors = StrategyGraph.find_closest_actor(
            actors_in_solution,
            possible_target_actors)
        assert len(target_actors) <= len(actors_in_solution)

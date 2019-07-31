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
        actors_in_solution = Actor.objects.all()
        possible_target_actors = Actor.objects.all()
        strategy = Strategy.objects.first()
        strategy_graph = StrategyGraph(strategy)
        target_actor = strategy_graph.find_closest_actor(
            actors_in_solution,
            possible_target_actors)
        assert target_actor.name == 'old_destination_actor'
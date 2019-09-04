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
        # this solution is not in the fixtures anymore
        pass
        #solutions = Solution.objects.all()
        #assert len(solutions) == 1
        #solution = Solution.objects.get(pk=89)
        #assert solution.name == "Simplified Peel Pioneer"

    def test_select_closest_actor(self):
        max_distance = 10000
        actors_in_solution = Actor.objects.filter(activity__id__lte=1845)
        possible_target_actors = Actor.objects.filter(activity__id__gte=1846)
        target_actors = StrategyGraph.find_closest_actor(
            actors_in_solution,
            possible_target_actors,
            absolute_max_distance=max_distance,
        )
        assert len(target_actors) <= len(actors_in_solution), \
               f'number of target actors found should be less or equal '\
               f'than the actors in solution for which a target actor '\
               f'was searched'
        actor_in_solution_set = set(
            actors_in_solution.values_list('id', flat=True))
        actors_found = set(target_actors.keys())
        assert actors_found <= actor_in_solution_set, \
               f'actors found_ {actors_found} must be a subset '\
               f'of the actors searched: {actor_in_solution_set}'

        possible_target_set = set(
            possible_target_actors.values_list('id', flat=True))
        chosen_target_set = set(target_actors.values())
        assert possible_target_set >= chosen_target_set, \
               f'chosen targets {chosen_target_set} has to be a subset of '\
               f'possible target actors {possible_target_set}'

        # test maximum distance for all actor pairs

        for actor_id1, actor_id2 in target_actors.items():
            actor1 = Actor.objects.get(id=actor_id1)
            actor2 = Actor.objects.get(id=actor_id2)
            pnt1 = actor1.administrative_location.geom.transform(3035,
                                                                 clone=True)
            pnt2 = actor2.administrative_location.geom.transform(3035,
                                                                 clone=True)

            assert pnt1.distance(pnt2) <= max_distance, \
                   f'distance between actor {actors1[i]} and {actors2[i]} '\
                   f'is {pnt1.distance(pnt2)} > {max_distance} (max_distance)'



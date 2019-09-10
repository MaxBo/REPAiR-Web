import random
from django.test import TestCase
from django.contrib.gis.geos import Point
from django.db.models import Count, Sum
from repair.apps.asmfa.models import (Actor, Activity, Actor2Actor,
                                      ActorStock, AdministrativeLocation,
                                      FractionFlow, Material)
from repair.apps.changes.models import Solution, Strategy
from repair.apps.asmfa.graphs.graph import StrategyGraph


class ClosestActorMixin:
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




class GraphWalkerTests(TestCase, ClosestActorMixin):
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


class MultiplyTestDataMixin:

    @classmethod
    def setUpTestData(cls):
        """multiply the test data for the peelpioneer_data"""
        n_clones = 50
        activities = Activity.objects.all()

        # clone actors
        new_actors = []
        new_stocks = []
        new_fraction_flows = []
        new_locations = []
        for activity in activities:
            actors = Actor.objects.filter(activity=activity)
            for actor in actors:
                for i in range(n_clones):
                    new_actor = Actor(
                        activity=actor.activity,
                        BvDid=actor.BvDid,
                        name=f'{actor.name}_{i}',
                        reason=actor.reason,
                        included=actor.included,
                        consCode=actor.consCode,
                        year=actor.year,
                        BvDii=actor.BvDii,
                        employees=actor.employees,
                        turnover=actor.turnover,
                        )
                    new_actors.append(new_actor)

                    # add new stocks
                    try:
                        old_stock = ActorStock.objects.get(origin=actor)
                        new_amount = (random.random() + 0.5) * old_stock.amount
                        new_stock = ActorStock(
                            origin=new_actor,
                            publication=old_stock.publication,
                            composition=old_stock.composition,
                            amount=new_amount,
                            keyflow=old_stock.keyflow,
                            year=old_stock.year,
                            waste=old_stock.Actor2Actor.objectswaste,
                        )
                        new_stocks.append(new_stock)

                        # add the fractionflow for the stocks
                        old_fraction_flow = FractionFlow.objects.get(
                            stock=old_stock)

                        new_fraction_flow = FractionFlow(
                            stock=new_stock,
                            origin=new_actor,
                            material=old_fraction_flow.material,
                            to_stock=True,
                            amount=new_amount,
                            publication=old_fraction_flow.publication,
                            avoidable=old_fraction_flow.avoidable,
                            hazardous=old_fraction_flow.hazardous,
                            nace=old_fraction_flow.nace,
                            composition_name=old_fraction_flow.composition_name,
                            strategy=old_fraction_flow.strategy,
                        )
                        new_fraction_flows.append(new_fraction_flow)

                    except (ActorStock.DoesNotExist,
                            FractionFlow.DoesNotExist):
                        # continue if no stock or fraction flow exists
                        pass


                    # add new locations
                    old_location = AdministrativeLocation.objects.filter(
                        actor=actor)
                    if old_location:
                        old_location = old_location[0]
                        #  spatial offset by +/- 0.01 degrees
                        dx = random.randint(-100, 100) / 10000.
                        dy = random.randint(-100, 100) / 10000.
                        geom = Point(x=old_location.geom.x + dx,
                                     y=old_location.geom.y + dy,
                                     srid=old_location.geom.srid)
                        new_location = AdministrativeLocation(
                            actor=new_actor,
                            area=old_location.area,
                            geom=geom)
                        new_locations.append(new_location)


        Actor.objects.bulk_create(new_actors)
        ActorStock.objects.bulk_create(new_stocks)
        AdministrativeLocation.objects.bulk_create(new_locations)

        #clone flows
        new_flows = []

        # get the different combinations of origin and destination activities
        origins_destinations = Actor2Actor.objects\
            .values('origin__activity',
                    'destination__activity')\
            .annotate(Count('id'))

        for origin_destination in origins_destinations:
            activity1 = Activity.objects.get(
                id=origin_destination['origin__activity'])
            activity2 = Activity.objects.get(
                id=origin_destination['destination__activity'])
            flows = Actor2Actor.objects.filter(origin__activity=activity1,
                                               destination__activity=activity2)
            fraction_flows = FractionFlow.objects.filter(
                origin__activity=activity1,
                destination__activity=activity2)
            fraction_flow_materials = fraction_flows\
                .values('material')\
                .annotate(Count('id'))\
                .annotate(Sum('amount'))
            total_amount = fraction_flows.aggregate(Sum('amount'))\
                ['amount__sum']

            source_actors = Actor.objects.filter(activity=activity1)
            destination_actors = Actor.objects.filter(activity=activity2)
            for flow in flows:
                for i in range(n_clones):
                    new_amount = (random.random() + 0.5) * flow.amount
                    new_flow = Actor2Actor(
                        origin=random.choice(source_actors),
                        destination=random.choice(destination_actors),
                        composition=flow.composition,
                        publication=flow.publication,
                        amount=new_amount,
                        waste=flow.waste,
                        process=flow.process,
                        keyflow=flow.keyflow,
                        year=flow.year,
                    )
                    new_flows.append(new_flow)

                    for fraction_flow_material in fraction_flow_materials:
                        material = Material.objects.get(
                            id=fraction_flow_material['material'])
                        fraction = (fraction_flow_material['amount__sum'] /
                                    total_amount)

                        new_fraction_flow = FractionFlow(
                            keyflow=new_flow.keyflow,
                            waste=new_flow.waste,
                            process=new_flow.process,
                            flow=new_flow,
                            origin=new_flow.origin,
                            destination=new_flow.destination,
                            material=material,
                            amount=new_amount * fraction,
                            publication=new_flow.publication,
                        )
                        new_fraction_flows.append(new_fraction_flow)

        Actor2Actor.objects.bulk_create(new_flows)
        FractionFlow.objects.bulk_create(new_fraction_flows)


class GraphWalkerPerformanceTests(MultiplyTestDataMixin,
                                  TestCase,
                                  ClosestActorMixin):
    """
    Testclass for performance tests of the graph walker

    loads the data for the peel pioneer example from a fixture
    and clone the data to get a big testcase
    """

    fixtures = ['peelpioneer_data']

    def test_cloned_actors_and_flows(self):
        # this solution is not in the fixtures anymore
        print(len(Actor.objects.all()))
        print(len(ActorStock.objects.all()))
        print(len(AdministrativeLocation.objects.all()))
        print(len(Actor2Actor.objects.all()))
        print(len(FractionFlow.objects.all()))



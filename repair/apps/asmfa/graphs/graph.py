from repair.apps.asmfa.models import (ActivityGroup, Activity, Actor2Actor,
                                      Actor, AdministrativeLocation)

class KeyflowGraph:
    def __init__(self, keyflow):
        self.keyflow = keyflow
        self.graph = self._keyflow_to_graph()

    def _keyflow_to_graph(self):
        # activitygroups in keyflow
        groups = ActivityGroup.objects.filter(keyflow=self.keyflow)
        # activities in keyflow, activities don't have a keyflow relation
        # themselves, but they relate to a group (which has a keyflow relation)
        activities = Activity.objects.filter(activitygroup__keyflow=self.keyflow)
        # that should return the same models
        activities = Activity.objects.filter(activitygroup__in=groups)
        # actors in keyflow
        actors = Actor.objects.filter(activity__activitygroup__keyflow=self.keyflow)
        # flows in keyflow, origin and destinations have to be
        # actors in the keyflow (actually one of both would suffice, as there
        # are no flows in between keyflows)
        flows = Actor2Actor.objects.filter(origin__in=actors,
                                           destination__in=actors)
        # example iteration over actors in keyflow
        # (maybe you can avoid iterations at all, they are VERY slow)
        for actor in actors:
            # location of an actor, django throws errors when none found (actor has no loaction),
            # kind of annoying
            try:
                location = AdministrativeLocation.objects.get(id=actor.id)
            except:
                # surprisingly many actors miss a location, shouldn't be that way
                print('no location for {}'.format(actor.name))
            # i forgot how to make the OR filter
            # flows leaving the actor, you can filter already filtered querysets again
            out_flows = flows.filter(origin=actor)
            # you could also do that (same, but example for attribute)
            out_flows = flows.filter(origin__id=actor.id)
            # flows going to actor
            in_flows = flows.filter(destination=actor)

        for flow in flows:
            # get a composition
            composition = flow.composition
            fractions = composition.fractions
            # the fractions relate to the composition, not the other way around,
            # so a reverse manager is used, that one can't be iterated
            # you can get the reverse related models this way
            fractions = fractions.all()
            for fraction in fractions:
                # the material
                material = fraction.material
                # the actual fraction of the fraction (great naming here)
                f = fraction.fraction

        return None


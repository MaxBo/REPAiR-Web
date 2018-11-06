from repair.apps.asmfa.models import (ActivityGroup, Activity, Actor2Actor,
                                      Actor)

class Graph:

    def keyflow_to_graph(self, keyflow):
        groups = ActivityGroup.objects.filter(keyflow=keyflow)
        activities = Activity.objects.filter(keyflow=keyflow)
        actors = Actor.objects.filter(activity__activitygroup__keyflow=keyflow)

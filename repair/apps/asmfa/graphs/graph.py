from repair.apps.asmfa.models import (ActivityGroup, Activity, Actor2Actor,
                                      Actor, AdministrativeLocation)
import graph_tool as gt
import graph_tool.draw
import numpy as np
import datetime
import cairo

class KeyflowGraph:
    def __init__(self, keyflow):
        self.keyflow = keyflow
        self.graph = self._keyflow_to_graph()

    def buildGraph(self, actors, flows):
        G = gt.Graph(directed=True)
        
        # Add the actors to the graph
        G.add_vertex(len(actors))
        vid = G.new_vertex_property("string")
        G.vertex_properties["id"] = vid

        actorids = {}
        for i in range(len(actors)):
        #for i, actor in enumerate(actors):
            G.vp.id[i] = actors[i].name
            actorids[actors[i].name] = i
        
        # Add the flows to the graph
        gflow = G.new_edge_property("object")
        eid = G.new_edge_property("int") # need a persistent edge id, because graph-tool can reindex the edges
        G.edge_properties["flow"] = gflow
        G.edge_properties["eid"] = eid

        for i in range(len(flows)):
        #for i, flow in enumerate(flows):
            # get the start and and actor id's
            v0 = actorids.get(str(flows[i].origin))
            v1 = actorids.get(str(flows[i].destination))

            if((v0 != None) & (v1 != None)):
                # create the flow in the graph and set the edge id
                G.add_edge(G.vertex(v0), G.vertex(v1))
                G.ep.eid[(v0,v1)] = i
                
                #G.ep.flow[(0,1)] = {'mass':95, 'composition':{'cucumber':0.3158, 'milk':0.6842}}
                
                fl = {}
                fl['mass'] = flows[i].amount
                fl['composition'] = {}
                # get a composition
                composition = flows[i].composition
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
                    fl['composition'][material] = f
                
                G.ep.flow[(v0,v1)] = fl
                G.ep.eid[(v0,v1)] = i

        t = (i for i in G.ep.flow)
        txt = G.new_edge_property("string", vals=t)        
        return gt.draw.graph_draw(G, vertex_size=20, vertex_text=G.vp.id,
                               vprops={"text_position":0, "font_weight": cairo.FONT_WEIGHT_BOLD, "font_size":14},
                               output_size=(700,600), output="test.png")
    
    def _keyflow_to_graph(self):
        # actors in keyflow
        actors = Actor.objects.filter(activity__activitygroup__keyflow=self.keyflow)
        # flows in keyflow, origin and destinations have to be
        # actors in the keyflow (actually one of both would suffice, as there
        # are no flows in between keyflows)
        flows = Actor2Actor.objects.filter(origin__in=actors,
                                           destination__in=actors)
        
        return self.buildGraph(actors, flows)
        
    def examples():
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
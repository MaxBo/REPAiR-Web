from repair.apps.asmfa.models import (Actor2Actor, Actor, KeyflowInCasestudy, 
                                      AdministrativeLocation)
from repair.apps.asmfa.graphs.graphwalker import GraphWalker
import graph_tool as gt
import graph_tool.draw
from django.db.models import Q
import numpy as np
import datetime
import cairo
from io import StringIO

class KeyflowGraph:
    def __init__(self, keyflow):
        self.keyflow = keyflow
        self._keyflow_to_graph()
        self.graphfile = "casestudy" + str(self.keyflow.casestudy.id) + "_keyflow" + str(self.keyflow.id) + ".gt"
    
    def _keyflow_to_graph(self):
        # get flows based on keyflow and filter actors
        self.flows = Actor2Actor.objects.filter(keyflow=self.keyflow)
        self.actors = Actor.objects.filter(Q(id__in=self.flows.values('origin_id')) | Q(id__in=self.flows.values('destination_id')))

    def buildGraph(self):
        actors = self.actors
        flows = self.flows
        
        g = gt.Graph(directed=True)
        
        # Add the actors to the graph
        g.add_vertex(len(actors))
        g.vertex_properties["id"] = g.new_vertex_property("int")
        g.vertex_properties["name"] = g.new_vertex_property("string")

        actorids = {}
        for i in range(len(actors)):
            g.vp.id[i] = actors[i].id
            g.vp.name[i] = actors[i].name
            actorids[actors[i].name] = i
        
        # Add the flows to the graph
        g.edge_properties["id"] = g.new_edge_property("int")
        g.edge_properties["flow"] = g.new_edge_property("object")
        g.edge_properties["eid"] = g.new_edge_property("int") # need a persistent edge id, because graph-tool can reindex the edges
       
        for i in range(len(flows)):
            # get the start and and actor id's
            v0 = actorids.get(str(flows[i].origin))
            v1 = actorids.get(str(flows[i].destination))

            if(v0 != None and v1 != None):            
                # create the flow in the graph and set the edge id
                edge = g.add_edge(g.vertex(v0), g.vertex(v1))
                g.ep.id[edge] = flows[i].id
                g.ep.eid[edge] = i
                # create dict with flow information
                fl = {}
                fl['amount'] = flows[i].amount
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
                    fl['composition'][material.name] = f

                g.ep.flow[(v0,v1)] = fl

        t = (i for i in g.ep.flow)
        txt = g.new_edge_property("string", vals=t)
        
        g.save(self.graphfile)
        # save graph image
        #pos = gt.draw.fruchterman_reingold_layout(g, n_iter=1000)
        #gt.draw.graph_draw(g, pos, vertex_size=20, vertex_text=g.vp.name, 
        #                       vprops={"text_position":0, "font_weight": cairo.FONT_WEIGHT_BOLD, "font_size":14},
        #                       output_size=(700,600), output="test.png")
        return g

    def calcGraph(self):
        g = gt.load_graph(self.graphfile)
        gw = GraphWalker(g)
        g2 = gw.calculate_solution(2.0)
        g2.save("casestudy" + str(self.keyflow.casestudy.id) + "_keyflow" + str(self.keyflow.id) + "_multiply2.gt")
        return g2
    
    def validateGraph(self):
        """Validate flows for a graph"""
        g = gt.load_graph(self.graphfile)
        invalid = []

        for e in g.edges():
            if(g.ep.flow[e] == None):
                flow = {}
                flow['flow_id'] = g.ep.id[e]
                flow['source_id'] = g.vp.id[e.source()]
                flow['source'] = g.vp.name[e.source()]
                flow['target_id'] = g.vp.id[e.target()]
                flow['target'] = g.vp.name[e.target()]
                invalid.append(flow)
        if len(invalid) != 0:
            return invalid
        else:
            return 'Graph is valid'
        
    def serialize(self, g):
        flows = []
        for e in g.edges():
            flow = {}
            flow['source_id'] = g.vp.id[e.source()]
            flow['source'] = g.vp.name[e.source()]
            flow['target_id'] = g.vp.id[e.target()]
            flow['target'] = g.vp.name[e.target()]
            flow['flow'] = g.ep.flow[e]
            flows.append(flow)
        return {'flows':flows}
        
    def examples():
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
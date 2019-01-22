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
from django.conf import settings
import os
from datetime import datetime


class KeyflowGraph:
    def __init__(self, keyflow):
        self.keyflow = keyflow
        path = settings.GRAPH_ROOT
        cspath = os.path.join(
            path, "casestudy{}".format(self.keyflow.casestudy.id))
        if not os.path.exists(cspath):
            os.makedirs(cspath)
        fn = "keyflow{}.gt".format(self.keyflow.id)
        self.graph_fn = os.path.join(cspath, fn)
    
    @property
    def date(self):
        if not self.exists:
            return None
        t = os.path.getmtime(self.graph_fn)
        return datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S') 
    
    @property
    def exists(self):
        return os.path.exists(self.graph_fn)
    
    def buildGraph(self):
        flows = Actor2Actor.objects.filter(keyflow=self.keyflow)
        actors = Actor.objects.filter(
            Q(id__in=flows.values('origin_id')) | 
            Q(id__in=flows.values('destination_id')))
        
        g = gt.Graph(directed=True)
        
        # Add the actors to the graph
        g.add_vertex(len(actors))
        g.vertex_properties["id"] = g.new_vertex_property("int")
        g.vertex_properties["bvdid"] = g.new_vertex_property("string")
        g.vertex_properties["name"] = g.new_vertex_property("string")

        actorids = {}
        for i in range(len(actors)):
            g.vp.id[i] = actors[i].id
            g.vp.bvdid[i] = actors[i].BvDid
            g.vp.name[i] = actors[i].name
            actorids[actors[i].id] = i
        
        # Add the flows to the graph
        g.edge_properties["id"] = g.new_edge_property("int")
        g.edge_properties["flow"] = g.new_edge_property("object")
        # need a persistent edge id, because graph-tool can reindex the edges
        g.edge_properties["eid"] = g.new_edge_property("int") 
       
        for i in range(len(flows)):
            # get the start and and actor id's
            v0 = actorids.get(flows[i].origin.id)
            v1 = actorids.get(flows[i].destination.id)

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
                # the fractions relate to the composition, not the other 
                # way around,
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
        
        g.save(self.graph_fn)
        # save graph image
        #pos = gt.draw.fruchterman_reingold_layout(g, n_iter=1000)
        #gt.draw.graph_draw(g, pos, vertex_size=20, vertex_text=g.vp.name, 
        #                       vprops={"text_position":0, "font_weight": cairo.FONT_WEIGHT_BOLD, "font_size":14},
        #                       output_size=(700,600), output="test.png")
        return g

    def calcGraph(self):
        g = gt.load_graph(self.graph_fn)
        gw = GraphWalker(g)
        g2 = gw.calculate_solution(2.0)
        g2.save("casestudy" + str(self.keyflow.casestudy.id) + "_keyflow" + str(self.keyflow.id) + "_multiply2.gt")
        return g2
    
    def validateGraph(self):
        """Validate flows for a graph"""
        g = gt.load_graph(self.graph_fn)
        invalid = []

        for e in g.edges():
            if(g.ep.flow[e] == None):
                flow = {}
                flow['flow_id'] = g.ep.id[e]
                flow['source_id'] = g.vp.id[e.source()]
                flow['source_bvdid'] = g.vp.bvdid[e.source()]
                flow['source'] = g.vp.name[e.source()]
                flow['target_id'] = g.vp.id[e.target()]
                flow['target_bvdid'] = g.vp.bvdid[e.target()]
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
            flow['source'] = g.vp.name[e.source()]
            flow['target'] = g.vp.name[e.target()]
            flow['flow'] = g.ep.flow[e]
            flows.append(flow)
        return {'flows':flows}
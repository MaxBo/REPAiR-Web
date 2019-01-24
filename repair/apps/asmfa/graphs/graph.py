from repair.apps.asmfa.models import (Actor2Actor, Actor, KeyflowInCasestudy,
                                      AdministrativeLocation, ActorStock)
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
from itertools import chain


class BaseGraph:
    def __init__(self, keyflow):
        self.keyflow = keyflow
        self.graph = None

    @property
    def path(self):
        path = settings.GRAPH_ROOT
        cspath = os.path.join(
            path, "casestudy-{}".format(self.keyflow.casestudy.id))
        if not os.path.exists(cspath):
            os.makedirs(cspath)
        return cspath

    @property
    def filename(self):
        fn = "keyflow-{}-base.gt".format(self.keyflow.id)
        return os.path.join(self.path, fn)

    @property
    def date(self):
        if not self.exists:
            return None
        t = os.path.getmtime(self.filename)
        return datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')

    @property
    def exists(self):
        return os.path.exists(self.filename)

    def load(self):
        self.graph = gt.load_graph(self.filename)
        return self.graph

    def save(self, graph=None):
        graph = graph or self.graph
        self.graph.save(self.filename)

    def build(self):
        actorflows = Actor2Actor.objects.filter(keyflow=self.keyflow)
        stockflows = ActorStock.objects.filter(keyflow=self.keyflow)
        actors = Actor.objects.filter(
            Q(id__in=actorflows.values('origin_id')) |
            Q(id__in=actorflows.values('destination_id')) |
            Q(id__in=stockflows.values('origin_id'))
        )
        flows = list(chain(actorflows, stockflows))
        
        self.graph = gt.Graph(directed=True)

        # Add the actors to the graph
        self.graph.add_vertex(len(actors))
        self.graph.vertex_properties["id"] = \
            self.graph.new_vertex_property("int")
        self.graph.vertex_properties["bvdid"] = \
            self.graph.new_vertex_property("string")
        self.graph.vertex_properties["name"] = \
            self.graph.new_vertex_property("string")

        actorids = {}
        #maxactorid = 0
        for i in range(len(actors)):
            self.graph.vp.id[i] = actors[i].id
            self.graph.vp.bvdid[i] = actors[i].BvDid
            self.graph.vp.name[i] = actors[i].name
            actorids[actors[i].id] = i
            #if(maxactorid < i):
                #maxactorid = i
        
        self.graph.add_vertex(len(stockflows))
        stockids = {}
        stockid = len(actorids)
        for i in range(len(stockflows)):
            # create a new vertex with name stock
            self.graph.vp.id[stockid] = stockid
            self.graph.vp.name[stockid] = "Stock " + stockflows[i].origin.name
            stockids[stockflows[i].origin.name] = stockid
            stockid = stockid + 1

        # Add the flows to the graph
        self.graph.edge_properties["id"] = self.graph.new_edge_property("int")
        self.graph.edge_properties["flow"] = \
            self.graph.new_edge_property("object")
        # need a persistent edge id, because graph-tool can reindex the edges
        self.graph.edge_properties["eid"] = self.graph.new_edge_property("int")
        
        for i in range(len(flows)):
            # get the start and and actor id's
            v0 = actorids.get(flows[i].origin.id)
            if(isinstance(flows[i], Actor2Actor)):
                v1 = actorids.get(flows[i].destination.id)
            else:
                v1 = stockids[flows[i].origin.name]

            if(v0 != None and v1 != None):
                # create the flow in the graph and set the edge id
                edge = self.graph.add_edge(
                    self.graph.vertex(v0), self.graph.vertex(v1))
                self.graph.ep.id[edge] = flows[i].id
                self.graph.ep.eid[edge] = i
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
                self.graph.ep.flow[(v0,v1)] = fl

        self.save()
        # save graph image
        #pos = gt.draw.fruchterman_reingold_layout(g, n_iter=1000)
        #gt.draw.graph_draw(g, pos, vertex_size=20, vertex_text=g.vp.name,
        #                       vprops={"text_position":0, "font_weight": cairo.FONT_WEIGHT_BOLD, "font_size":14},
        #                       output_size=(700,600), output="test.png")
        return self.graph

    def validate(self):
        """Validate flows for a graph"""
        invalid = []
        self.load()

        for e in self.graph.edges():
            if(self.graph.ep.flow[e] == None):
                flow = {}
                flow['flow_id'] = self.graph.ep.id[e]
                flow['source_id'] = self.graph.vp.id[e.source()]
                flow['source_bvdid'] = self.graph.vp.bvdid[e.source()]
                flow['source'] = self.graph.vp.name[e.source()]
                flow['target_id'] = self.graph.vp.id[e.target()]
                flow['target_bvdid'] = self.graph.vp.bvdid[e.target()]
                flow['target'] = self.graph.vp.name[e.target()]
                invalid.append(flow)
        if len(invalid) != 0:
            return invalid
        else:
            return 'Graph is valid'

    def serialize(self):
        flows = []
        if not self.graph:
            self.load()
        for e in self.graph.edges():
            flow = {}
            flow['source'] = self.graph.vp.name[e.source()]
            flow['target'] = self.graph.vp.name[e.target()]
            flow['flow'] = self.graph.ep.flow[e]
            flows.append(flow)
        return {'flows':flows}


class StrategyGraph(BaseGraph):
    def __init__(self, strategy):
        self.keyflow = strategy.keyflow
        self.strategy = strategy

    @property
    def filename(self):
        fn = "keyflow-{}-s{}.gt".format(self.keyflow.id, self.strategy.id)
        return os.path.join(self.path, fn)

    def build(self):
        base_graph = BaseGraph(self.keyflow)
        if not base_graph.exists:
            raise FileNotFoundError
        g = base_graph.load()
        gw = GraphWalker(g)
        self.graph = gw.calculate_solution(2.0)
        self.graph.save(self.filename)
        return self.graph

    def to_queryset(self):
        if not self.graph:
            self.load()

        for e in self.graph.edges():
            flow = {}
            flow['source'] = self.graph.vp.name[e.source()]
            flow['target'] = self.graph.vp.name[e.target()]
            flow['flow'] = self.graph.ep.flow[e]
            flows.append(flow)
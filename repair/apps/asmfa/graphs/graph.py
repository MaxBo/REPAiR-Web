from repair.apps.asmfa.models import (Actor2Actor, FractionFlow, Actor,
                                      ActorStock, Material,
                                      StrategyFractionFlow)
from repair.apps.changes.models import (SolutionInStrategy,
                                        ImplementationQuantity,
                                        AffectedFlow)
from repair.apps.utils.utils import descend_materials
from repair.apps.asmfa.graphs.graphwalker import GraphWalker
try:
    import graph_tool as gt
    from graph_tool import stats as gt_stats
    from graph_tool import draw, util
    import cairo
except ModuleNotFoundError:
    pass
from django.db.models import Q
import numpy as np
import datetime
from io import StringIO
from django.conf import settings
import os
from datetime import datetime
from itertools import chain

import time


class BaseGraph:
    def __init__(self, keyflow, tag=''):
        self.keyflow = keyflow
        self.tag = tag
        self.graph = None

    @property
    def path(self):
        path = settings.GRAPH_ROOT
        cspath = os.path.join(
            path, f"{self.tag}casestudy-{self.keyflow.casestudy.id}")
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

    def remove(self):
        self.graph = None
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def build(self):
        actorflows = FractionFlow.objects.filter(
            keyflow=self.keyflow, to_stock=False)
        stockflows = FractionFlow.objects.filter(
            keyflow=self.keyflow, to_stock=True)
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
        for i in range(len(actors)):
            self.graph.vp.id[i] = actors[i].id
            self.graph.vp.bvdid[i] = actors[i].BvDid
            self.graph.vp.name[i] = actors[i].name
            actorids[actors[i].id] = i

        # Add the flows to the graph
        # need a persistent edge id, because graph-tool can reindex the edges
        self.graph.edge_properties["id"] = self.graph.new_edge_property("int")
        self.graph.edge_properties['amount'] = \
            self.graph.new_edge_property("float")
        self.graph.edge_properties['material'] = \
            self.graph.new_edge_property("int")
        self.graph.edge_properties['process'] = \
            self.graph.new_edge_property("int")

        for i in range(len(flows)):
            # get the start and and actor id's
            flow = flows[i]
            v0 = actorids.get(flow.origin.id)
            if not flow.to_stock:
                v1 = actorids.get(flow.destination.id)
            else:
                v1 = v0

            if (v0 != None and v1 != None):
                e = self.graph.add_edge(
                    self.graph.vertex(v0), self.graph.vertex(v1))
                self.graph.ep.id[e] = flow.id
                self.graph.ep.material[e] = flow.material_id
                self.graph.ep.process[e] = \
                    flow.process_id if flow.process_id is not None else - 1
                self.graph.ep.amount[e] = flow.amount

        self.save()
        # save graph image
        #fn = "keyflow-{}-base.png".format(self.keyflow.id)
        #fn = os.path.join(self.path, fn)
        #pos = gt.draw.fruchterman_reingold_layout(self.graph, n_iter=1000)
        #gt.draw.graph_draw(self.graph, pos, vertex_size=20,
        # vertex_text=self.graph.vp.name,
        #                       vprops={"text_position":0,
        # "font_weight": cairo.FONT_WEIGHT_BOLD, "font_size":14},
        #                       output_size=(700,600), output=fn)
        return self.graph

    def validate(self):
        """Validate flows for a graph"""
        invalid = []
        self.load()

        if self.graph.num_vertices() < 1:
            return 'Graph is invalid, no vertices'

        if self.graph.num_edges() < 1:
            return 'Graph is invalid, no edges'

        for v in self.graph.vertices():
            if(v.in_degree() + v.out_degree() == 0):
                invalid.append(v)

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
            flow['id'] = self.graph.ep.id[e]
            flow['source'] = self.graph.vp.id[e.source()]
            flow['target'] = self.graph.vp.id[e.target()]
            flow['material'] = self.graph.ep.material[e]
            flow['amount'] = self.graph.ep.amount[e]
            flows.append(flow)
        return {'flows':flows}


class StrategyGraph(BaseGraph):
    def __init__(self, strategy, tag=''):
        self.keyflow = strategy.keyflow
        self.strategy = strategy
        self.tag = tag
        self.graph = None

    @property
    def filename(self):
        fn = f"{self.tag}keyflow-{self.keyflow.id}-s{self.strategy.id}.gt"
        return os.path.join(self.path, fn)

    @property
    def exists(self):
        return os.path.exists(self.filename)

    def load(self):
        self.graph = gt.load_graph(self.filename)
        return self.graph

    def mock_changes(self):
        '''make some random changes for testing'''
        flows = FractionFlow.objects.filter(
            keyflow=self.keyflow, destination__isnull=False)
        flow_ids = np.array(flows.values_list('id', flat=True))
        # pick 30% of the flows for change of amount
        choice = np.random.choice(
            a=[False, True], size=len(flow_ids), p=[0.7, 0.3])
        picked_flows = flows.filter(id__in=flow_ids[choice])
        strat_flows = []
        for flow in picked_flows:
            # vary between -25% and +25%
            new_amount = flow.amount * (1 + (np.random.random() / 2 - 0.25))
            strat_flow = StrategyFractionFlow(
                strategy=self.strategy, amount=new_amount, fractionflow=flow)
            strat_flows.append(strat_flow)
        StrategyFractionFlow.objects.bulk_create(strat_flows)

        # pick 5% of flows as base for new flows
        choice = np.random.choice(
            a=[False, True], size=len(flow_ids), p=[0.95, 0.05])
        picked_flows = flows.filter(id__in=flow_ids[choice])
        actors = Actor.objects.filter(
            activity__activitygroup__keyflow=self.keyflow)
        actor_ids = np.array(actors.values_list('id', flat=True))
        picked_actor_ids = np.random.choice(a=actor_ids, size=len(picked_flows))
        for i, flow in enumerate(picked_flows):
            change_origin = np.random.randint(2)
            new_target = actors.get(id=picked_actor_ids[i])
            # unset id
            flow.pk = None
            flow.strategy = self.strategy
            flow.origin = flow.origin if not change_origin else new_target
            flow.destination = flow.destination if change_origin else new_target
            flow.amount += flow.amount * (np.random.random() / 2 - 0.25)
            flow.save()

    def create_new_flows(self, solution_part, g):
        # shift actor flows to new origin or target and create new FractionFlow
        # get actorflows that belong to the implementation flow
        if not solution_part.references_part:
            actors_origin = Actor.objects.filter(
                activity=solution_part.implementation_flow_origin_activity)
            actors_destination = Actor.objects.filter(
                activity=solution_part.implementation_flow_destination_activity)
            materials = descend_materials(
                [solution_part.implementation_flow_material])
            actorflows = FractionFlow.objects.filter(
               origin__in=actors_origin.values('id'),
               destination__in=actors_destination.values('id'),
               material__in=materials)
        # ToDo:
        else:
            pass

        # add Actors related to SolutionPart.new_target_activity
        new_actors = Actor.objects.filter(
            activity=solution_part.new_target_activity)
        count = len(new_actors)
        targets = []
        for actor in new_actors:
            vertices = util.find_vertex(g, g.vp['id'], actor.id)
            # check if vertex exists, else create new
            if(len(vertices) > 0):
                v = vertices[0]
            else:
                v = g.add_vertex()
                g.vp.id[v] = actor.id
                g.vp.bvdid[v] = actor.BvDid
                g.vp.name[v] = actor.name
            targets.append({"actor": actor, "vertex": v})

        # add edges related to the new ImplementationFlow
        # this is skipped when the new_target_activity related flows
        # are already in the graph
        for flow in actorflows:
            amount = flow.amount / count
            # Change flow in the graph
            edges = util.find_edge(g, g.ep['id'], flow.id)
            if len(edges) > 1:
                raise ValueError("FractionFlow.id ", flow.id,
                                 " is not unique in the graph")
            elif len(edges) == 0:
                print("Cannot find FractionFlow.id ", flow.id, " in the graph")
            else:
                edge_del = edges[0]
                for target in targets:
                    # make the new edge and FractionFlow
                    if solution_part.keep_origin:
                        # keep origin of flow
                        origin = flow.origin
                        destination = target["actor"]
                        e = g.add_edge(edge_del.source(), target["vertex"])
                    else:
                        # keep destination of flow
                        origin = target["actor"]
                        destination = flow.destination
                        e = g.add_edge(target["vertex"], edge_del.target())

                    # ToDo: actually don't do this, only after all calculations
                    # create a new fractionflow for the implementation flow
                    ff = FractionFlow(origin=origin,
                                      destination=destination,
                                      flow = flow.flow,
                                      stock = flow.stock,
                                      material = flow.material,
                                      to_stock = flow.to_stock,
                                      amount = amount,
                                      publication = flow.publication,
                                      avoidable = flow.avoidable,
                                      hazardous = flow.hazardous,
                                      nace = flow.nace,
                                      composition_name = flow.composition_name,
                                      strategy = self.strategy,
                                      keyflow = flow.keyflow,
                                      description = flow.description,
                                      year = flow.year,
                                      waste = flow.waste,
                                      process = flow.process
                                      )
                    ff.save()

                    g.ep.id[e] = ff.id
                    g.ep.amount[e] = amount
                    g.ep.material[e] = flow.material.id
                    g.ep.process[e] = \
                        flow.process.id if flow.process is not None else - 1
                # remove the edge from the graph
                g.remove_edge(edge_del)
                # set the StrategyFractionFlow.amount to 0
                sff = StrategyFractionFlow.objects.update_or_create(
                    fractionflow=flow,
                    strategy=self.strategy,
                    material=flow.material,
                    defaults={"amount" : 0})

    def mock_changes(self):
        '''make some random changes for testing'''
        flows = FractionFlow.objects.filter(
            keyflow=self.keyflow, destination__isnull=False)
        flow_ids = np.array(flows.values_list('id', flat=True))
        # pick 30% of the flows for change of amount
        choice = np.random.choice(
            a=[False, True], size=len(flow_ids), p=[0.7, 0.3])
        picked_flows = flows.filter(id__in=flow_ids[choice])
        strat_flows = []
        for flow in picked_flows:
            # vary between -25% and +25%
            new_amount = flow.amount * (np.random.random() / 2 - 0.25)
            strat_flow = StrategyFractionFlow(
                strategy=self.strategy, amount=new_amount, fractionflow=flow)
            strat_flows.append(strat_flow)
        StrategyFractionFlow.objects.bulk_create(strat_flows)

        # pick 5% of flows as base for new flows
        choice = np.random.choice(
            a=[False, True], size=len(flow_ids), p=[0.95, 0.05])
        picked_flows = flows.filter(id__in=flow_ids[choice])
        actors = Actor.objects.filter(
            activity__activitygroup__keyflow=self.keyflow)
        actor_ids = np.array(actors.values_list('id', flat=True))
        picked_actor_ids = np.random.choice(a=actor_ids, size=len(picked_flows))
        for i, flow in enumerate(picked_flows):
            change_origin = np.random.randint(2)
            new_target = actors.get(id=picked_actor_ids[i])
            # unset id
            flow.pk = None
            flow.strategy = self.strategy
            flow.origin = flow.origin if not change_origin else new_target
            flow.destination = flow.destination if change_origin else new_target
            flow.amount += flow.amount * (np.random.random() / 2 - 0.25)
            flow.save()

    def clean(self):
        '''
        wipe all related StrategyFractionFlows
        and related new FractionFlows
        '''
        flows = FractionFlow.objects.filter(strategy=self.strategy)
        flows.delete()
        modified = StrategyFractionFlow.objects.filter(strategy=self.strategy)
        modified.delete()

    def build(self):

        base_graph = BaseGraph(self.keyflow, tag=self.tag)
        if not base_graph.exists:
            raise FileNotFoundError
        g = base_graph.load()
        gw = GraphWalker(g)

        self.clean()
        #self.mock_changes()

        # add change attribute, it defaults to 0.0
        g.ep.change = g.new_edge_property("float")
        # add include attribute, it defaults to False
        g.ep.include = g.new_edge_property("bool")

        # get the solutions in this strategy and order them by priority
        solutions_in_strategy = SolutionInStrategy.objects.filter(
            strategy=self.strategy).order_by('priority')
        for solution_in_strategy in solutions_in_strategy.order_by('priority'):
            solution = solution_in_strategy.solution
            parts = solution.solution_parts.all()
            # get the solution parts using the reverse relation
            for solution_part in parts.order_by('priority'):
                if solution_part.implements_new_flow:
                    self.create_new_flows(solution_part, g)

                # set the AffectedFlow include property to true
                affectedflows = AffectedFlow.objects.filter(
                    solution_part=solution_part)
                # get FractionFlows related to AffectedFlow
                affectedfractionflows = FractionFlow.objects.none()
                for af in affectedflows:
                    # get actorflows for each AffectedFlow
                    actors_origin = Actor.objects.filter(
                        activity=af.origin_activity)
                    actors_destination = Actor.objects.filter(
                        activity=af.destination_activity)

                    materials = descend_materials(
                        [solution_part.implementation_flow_material])
                    affectedfractionflows = \
                        affectedfractionflows | FractionFlow.objects.filter(
                            origin__in=actors_origin.values('id'),
                            destination__in=actors_destination.values('id'),
                            material__in=materials)

                # ToDo: filter instead of iterating?
                start = time.time()

                # exclude all
                g.ep.include.a[:] = False
                # include affected edges
                for flow in affectedfractionflows:
                    edges = util.find_edge(g, g.ep['id'], flow.id)
                    if len(edges) > 0:
                        g.ep.include[edges[0]] = True
                    else:
                        print('Warning: base graph is missing affected flows')
                #for e in g.edges():
                    #source = g.vp.id[e.source()]
                    #target = g.vp.id[e.target()]
                    #ff = affectedfractionflows.filter(origin_id=source,
                                              #destination_id=target)
                    #if(ff.count() > 0):
                        #g.ep.include[e] = True
                    #else:
                        #g.ep.include[e] = False
                end = time.time()
                print(end-start)
                # get the implementation and its quantity
                quantity = ImplementationQuantity.objects.get(
                    question=solution_part.question,
                    implementation=solution_in_strategy)

                # ToDo: SolutionInStrategy geometry for filtering?
                gw = GraphWalker(g)
                self.graph = gw.calculate_solution_part(
                    solution_part, affectedfractionflows, quantity)

            # store the changes for this solution into amount
            self.graph = gw.add_changes_to_amounts()

        # save the strategy graph to a file
        self.graph.save(self.filename)

        # save modifications and new flows into database
        self.translate_to_db()
        return self.graph

    def translate_to_db(self):
        # store edges (flows) to database
        for e in self.graph.edges():
            amount_new = self.graph.ep.amount[e]
            # get the related FractionFlow
            ff = FractionFlow.objects.get(id=self.graph.ep.id[e])
            if ff.amount != amount_new:
                # update or create a strategyfractionflow to store the amount
                sff = StrategyFractionFlow.objects.update_or_create(
                    fractionflow=ff,
                    strategy=self.strategy,
                    material=ff.material,
                    defaults={"amount" : amount_new}
                )
            else:
                # delete strategyfractionflow if amount is same as fractionflow
                StrategyFractionFlow.objects.filter(
                    fractionflow=ff,
                    strategy=self.strategy,
                    material=ff.material
                    ).delete()

    def to_queryset(self):
        if not self.graph:
            self.load()

        for e in self.graph.edges():
            flow = {}
            flow['id'] = self.graph.ep.id[e]
            flow['source'] = self.graph.vp.id[e.source()]
            flow['target'] = self.graph.vp.id[e.target()]
            flow['material'] = self.graph.ep.material[e]
            flow['amount'] = self.graph.ep.amount[e]
            flows.append(flow)
from repair.apps.asmfa.models import (Actor2Actor, FractionFlow, Actor,
                                      ActorStock, Material,
                                      StrategyFractionFlow)

from repair.apps.changes.models import (SolutionInStrategy, 
                                        ImplementationQuantity,
                                        AffectedFlow)
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
        actorflows = FractionFlow.objects.filter(keyflow=self.keyflow, to_stock=False)
        stockflows = FractionFlow.objects.filter(keyflow=self.keyflow, to_stock=True)
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
        self.graph.edge_properties['amount'] = self.graph.new_edge_property("int")
        self.graph.edge_properties['material'] = self.graph.new_edge_property("string")

        for i in range(len(flows)):
            # get the start and and actor id's
            flow = flows[i]
            v0 = actorids.get(flow.origin.id)
            if not flow.to_stock:
                v1 = actorids.get(flow.destination.id)
            else:
                v1 = v0

            if (v0 != None and v1 != None and isinstance(flows[i], FractionFlow)):
                e = self.graph.add_edge(
                    self.graph.vertex(v0), self.graph.vertex(v1))
                self.graph.ep.id[e] = flows[i].id
                self.graph.ep.material[e] = flows[i].material
                self.graph.ep.amount[e] = flows[i].amount

        self.save()
        # save graph image
        #fn = "keyflow-{}-base.png".format(self.keyflow.id)
        #fn = os.path.join(self.path, fn)        
        #pos = gt.draw.fruchterman_reingold_layout(self.graph, n_iter=1000)
        #gt.draw.graph_draw(self.graph, pos, vertex_size=20, vertex_text=self.graph.vp.name,
        #                       vprops={"text_position":0, "font_weight": cairo.FONT_WEIGHT_BOLD, "font_size":14},
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
    def __init__(self, strategy):
        self.keyflow = strategy.keyflow
        self.strategy = strategy
        self.graph = None

    @property
    def filename(self):
        fn = "keyflow-{}-s{}.gt".format(self.keyflow.id, self.strategy.id)
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
        actors_origin = Actor.objects.filter(
            activity=solution_part.implementation_flow_origin_activity)
        actors_destination = Actor.objects.filter(
            activity=solution_part.implementation_flow_destination_activity)
        actorflows = FractionFlow.objects.filter(
           Q(origin__in=actors_origin.values('id')) &
           Q(destination__in=actors_destination.values('id')),
           material=solution_part.implementation_flow_material)
        
        # add Actors related to SolutionPart.new_target_activity
        new_actors = Actor.objects.filter(
            activity=solution_part.new_target_activity)
        count = len(new_actors)
        targets = []
        for actor in new_actors:
            #TODO: check if vertext exists
            v = g.add_vertex()
            g.vp.id[v] = actor.id
            g.vp.bvdid[v] = actor.BvDid
            g.vp.name[v] = actor.name
            targets.append({"actor": actor, "vertex": v})
            
        # add edges related to the new ImplementationFlow
        # this is skipped when the new_target_activity related flows are allready in the graph
        for flow in actorflows:
            amount = flow.amount / count
            # Change flow in the graph
            edges = util.find_edge(g, g.ep['id'], flow.id)
            if len(edges) > 1:
                raise ValueError("FractionFlow.id ", flow.id, " is not unique in the graph")
            elif len(edges) == 0:
                print("Cannot find FractionFlow.id ", flow.id, " in the graph")
            else:
                edge_del = edges[0]
                for target in targets:
                    correct_target = False
                    # make the new edge and FractionFlow
                    if solution_part.keep_origin:
                        # check if the origin of the flow is equal to origin of graph edge 
                        if flow.origin.id == edge_del.source():
                            # keep origin of flow
                            origin = flow.origin
                            destination = target["actor"]
                            e = g.add_edge(edge_del.source(), target["vertex"])
                            correct_target = True
                    else:
                        if flow.destination.id == edge_del.target():
                            # keep destination of flow
                            origin = target["actor"]
                            destination = flow.destination
                            e = g.add_edge(target["vertex"], edge_del.target())
                            correct_target = True
                    
                    if correct_target:
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
                                            strategy = flow.strategy,
                                            keyflow = flow.keyflow,
                                            description = flow.description,
                                            year = flow.year,
                                            waste = flow.waste,
                                            process = flow.process
                                            )
                        ff.save()
                        
                        
                        g.ep.amount[e] = amount
                        g.ep.material[e] = flow.material
                        # set the newflow property; needed for storing the changes to db
                        g.ep.newflow[e] = True
                g.remove_edge(edge_del)

    def build(self):
        if self.exists:
            self.load()
        else:
            # get the base graph
            base_graph = BaseGraph(self.keyflow)
            if not base_graph.exists:
                base_graph.build()
            g = base_graph.load()
            msg = base_graph.validate()
            if msg != 'Graph is valid':
                print(msg)
            
            # add change attribute, it defaults to 0.0
            g.ep.change = g.new_edge_property("float")
            # add newflow attribute, it defaults to False
            g.ep.newflow = g.new_edge_property("bool")
            # add include attribute, it defaults to False
            g.ep.include = g.new_edge_property("bool")
            gw = GraphWalker(g)
            
            # get the solutions in this strategy and order them by priority
            solutions_in_strategy = SolutionInStrategy.objects.filter(strategy=self.strategy).order_by('priority')
            for solution_in_strategy in solutions_in_strategy:
                solution = solution_in_strategy.solution
                # get the solution parts using the reverse relation
                for solution_part in solution.solution_parts.all():
                    if solution_part.implements_new_flow:
                        self.create_new_flows(solution_part, g)
                                    
                    # set the AffectedFlow include property to true
                    affectedflows = AffectedFlow.objects.filter(solution_part=solution_part)
                    # get FractionFlows related to AffectedFlow
                    affectedfractionflows = FractionFlow.objects.none()
                    for af in affectedflows:
                        # get actorflows for each AffectedFlow
                        actors_origin = Actor.objects.filter(
                            activity=af.origin_activity)
                        actors_destination = Actor.objects.filter(
                            activity=af.destination_activity)
                        
                        affectedfractionflows = affectedfractionflows | FractionFlow.objects.filter(
                                                  Q(origin__in=actors_origin.values('id')) &
                                                  Q(destination__in=actors_destination.values('id')),
                                                  material=solution_part.implementation_flow_material)

                    for e in g.edges():
                        source = g.vp.id[e.source()]
                        target = g.vp.id[e.target()]
                        ff = affectedfractionflows.filter(origin_id=source,
                                                  destination_id=target)
                        if(ff.count() > 0):
                            g.ep.include[e] = True
                        else:
                            g.ep.include[e] = False
                    
                    # get the implementation and its quantity
                    quantity = ImplementationQuantity.objects.get(
                        question=solution_part.question,
                        implementation=solution_in_strategy)
                    ## get actorflows
                    #actors_origin = Actor.objects.filter(
                        #activity=solution_part.implementation_flow_origin_activity)
                    #actors_destination = Actor.objects.filter(
                        #activity=solution_part.implementation_flow_destination_activity)
                    #actorflows = FractionFlow.objects.filter(
                        #Q(origin__in=actors_origin.values('id')) &
                        #Q(destination__in=actors_destination.values('id')),
                        #material=solution_part.implementation_flow_material)

                    # ToDo: SolutionInStrategy geometry for filtering?
                    self.graph = gw.calculate_solution_part(solution_part, affectedfractionflows, quantity)
            
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
                StrategyFractionFlow.objects.update_or_create(fractionflow=ff,
                                                              strategy=self.strategy,
                                                              material=ff.material,
                                                              defaults={"amount" : amount_new})
            else:
                # delete strategyfractionflow if amount is same as fractionflow
                StrategyFractionFlow.objects.filter(fractionflow=ff,
                                                    strategy=self.strategy,
                                                    material=ff.material).delete()

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
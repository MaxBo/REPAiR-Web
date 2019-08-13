from repair.apps.asmfa.models import (Actor2Actor, FractionFlow, Actor,
                                      ActorStock, Material,
                                      StrategyFractionFlow)
from repair.apps.changes.models import (SolutionInStrategy,
                                        ImplementationQuantity,
                                        AffectedFlow, Scheme,
                                        ImplementationArea)
from repair.apps.statusquo.models import SpatialChoice
from repair.apps.utils.utils import descend_materials
from repair.apps.asmfa.graphs.graphwalker import GraphWalker
try:
    import graph_tool as gt
    from graph_tool import stats as gt_stats
    from graph_tool import draw, util
    import cairo
except ModuleNotFoundError:
    pass
from django.db.models import Q, Sum
import numpy as np
import datetime
from io import StringIO
from django.conf import settings
import os
from datetime import datetime
from itertools import chain

import time


class Formula:
    def __init__(self, a=1, b=0, q=0, is_absolute=False):
        '''
        linear change calculation

        absolute change:
        v’ = v + delta
        delta = a * q + b

        relative change:
        v’ = v * factor
        factor = a * q + b

        Parameters
        ----------
        a: float, optional
           by default 1
        q: float, optional
           quantity (user input), by default 0
        b: float, optional
           by default 0
        is_absolute: bool, optional
           absolute change, by default False
        '''
        self.a = a
        self.b = b
        self.q = q
        self.is_absolute = is_absolute

    @classmethod
    def from_implementation(self, solution_part, implementation):
        question = solution_part.question
        is_absolute = solution_part.is_absolute
        a = solution_part.a
        b = solution_part.b
        q = 0

        if question:
            quantity = ImplementationQuantity.objects.get(
                question=solution_part.question,
                implementation=implementation)
            # question overrides is_absolute of part
            is_absolute = question.is_absolute
            q = quantity.value

        formula = Formula(a=a, b=b, q=q, is_absolute=is_absolute)

        return formula

    def calculate(self, v):
        '''
        Parameters
        ----------
        v: float,
           value to apply formula to

        Returns
        -------
        v': float
            calculated value
        '''
        return self.calculate_factor(v) * v

    def calculate_delta(self, v):
        '''
        Parameters
        ----------
        v: float,
           value to apply formula to

        Returns
        -------
        delta: float
           signed delta
        '''
        return self.calculate(v) - v

    def calculate_factor(self, v=None):
        '''
        Parameters
        ----------
        v: float, optional
           needed for calculation of a

        Returns
        -------
        factor: float
            calculated factor
        '''
        if self.is_absolute:
            if v is None:
                raise ValueError('Value needed for calculation of a factor for '
                                 'absolute changes')
            delta = self.a * self.q + self.b
            v_ = v + delta
            factor = v_ / v
        else:
            factor = self.a * self.q + self.b
        return factor


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

    def create_new_flows(self, implementation_flows, target_actor,
                         graph, formula, material=None, keep_origin=True):
        '''
        creates new flows based on given implementation flows and redirects them
        to target actor (either origin or destinations are changing)
        implementation_flows stay untouched
        graph is updated in place
        Warning: side effects on implementation_flows
        '''
        new_flows = []

        target_vertex = util.find_vertex(graph, graph.vp['id'], target_actor.id)
        if(len(target_vertex) > 0):
            target_vertex = target_vertex[0]
        else:
            target_vertex = graph.add_vertex()
            graph.vp.id[target_vertex] = target_actor.id
            graph.vp.bvdid[target_vertex] = target_actor.BvDid
            graph.vp.name[target_vertex] = target_actor.name

        if formula.is_absolute:
            total = implementation_flows.aggregate(total=Sum('amount'))['total']
            new_total = formula.calculate(total)

        # create new flows and add corresponding edges
        for flow in implementation_flows:
            # ToDo: new flows keep the amount, they are reduced in the
            # calculation ??? how does this affect the other flows?
            # absolute change?
            # flow.save()

            # equally distribute amounts
            amount = formula.calculate(flow.amount) / len(implementation_flows)

            if formula.is_absolute:
                # distribute total change to changes on edges
                # depending on share of total
                solution_factor = new_total * amount / total
            else:
                amount = formula.calculate(flow.amount)

            # Change flow in the graph
            edges = util.find_edge(graph, graph.ep['id'], flow.id)
            if len(edges) > 1:
                raise ValueError("FractionFlow.id ", flow.id,
                                 " is not unique in the graph")
            elif len(edges) == 0:
                print("Cannot find FractionFlow.id ", flow.id, " in the graph")
                continue
            edge = edges[0]
            if keep_origin:
                new_edge = graph.add_edge(edge.source(), target_vertex)
            else:
                new_edge = graph.add_edge(target_vertex, edge.target())

            # create a new fractionflow for the implementation flow
            # setting id to None creates new one when saving
            # while keeping attributes
            flow.id = None
            flow.amount = amount
            if keep_origin:
                flow.destination = target_actor
            else:
                flow.origin = target_actor
            # strategy marks flow as new flow
            flow.strategy = self.strategy
            flow.save()
            new_flows.append(flow)

            graph.ep.id[new_edge] = flow.id
            graph.ep.amount[new_edge] = amount
            # ToDo: swap material
            graph.ep.material[new_edge] = flow.material.id
            graph.ep.process[new_edge] = \
                flow.process.id if flow.process is not None else - 1

        # return new_flows

        # return empty list for now
        return []

    def clean(self):
        '''
        wipe all related StrategyFractionFlows
        and related new FractionFlows
        '''
        flows = FractionFlow.objects.filter(strategy=self.strategy)
        flows.delete()
        modified = StrategyFractionFlow.objects.filter(strategy=self.strategy)
        modified.delete()

    def _get_referenced_flows(self, flow_reference, implementation):
        '''
        return flows on actor level filtered by flow_reference attributes
        and implementation areas
        '''
        #impl_materials = descend_materials(
            #[flow_reference.material])

        origins = Actor.objects.filter(
            activity=flow_reference.origin_activity)
        # filter by origin area
        if flow_reference.origin_area:
            # implementation area
            implementation_area = flow_reference.origin_area\
                .implementationarea_set.get(implementation=implementation)
            # if user didn't draw sth. take poss. impl. area instead
            geom = implementation_area.geom or flow_reference.origin_area.geom
            origins = origins.filter(
                        administrative_location__geom__intersects=geom)
        destinations = Actor.objects.filter(
            activity=flow_reference.destination_activity)
        # filter by destination area
        if flow_reference.destination_area:
            implementation_area = flow_reference.destination_area\
                .implementationarea_set.get(implementation=implementation)
            geom = implementation_area.geom or \
                flow_reference.destination_area.geom
            destinations = destinations.filter(
                        administrative_location__geom__intersects=geom)
        reference_flows = FractionFlow.objects.filter(
            origin__in=origins,
            destination__in=destinations,
            material=flow_reference.material
        )
        return reference_flows

    def _get_affected_flows(self, solution_part):
        '''
        filters flows by definitions in solution part
        return tuple (implementation flows, affected flows)
        '''
        # set the AffectedFlow include property to true
        affectedflows = AffectedFlow.objects.filter(
                        solution_part=solution_part)
        # get FractionFlows related to AffectedFlow
        affected_flows = FractionFlow.objects.none()
        for af in affectedflows:
            materials = descend_materials([af.material])
            affected_flows = \
                affected_flows | FractionFlow.objects.filter(
                    origin__activity=af.origin_activity,
                    destination__activity=af.destination_activity,
                    material__in=materials)
        return affectedflows

    def _include(self, graph, flows, do_include=True):
        '''
        include flows in graph, excludes all others
        set do_include=False to exclude
        graph is changed in place
        '''
        start = time.time()
        # include affected edges
        edges = self._get_edges(graph, flows)
        for edge in edges:
            graph.ep.include[edge] = do_include
        end = time.time()

    def _reset_include(self, graph, do_include=True):
        # exclude all
        graph.ep.include.a[:] = do_include

    def _get_edges(self, graph, flows):
        edges = []
        for flow in flows:
            e = util.find_edge(graph, graph.ep['id'], flow.id)
            if len(e) > 0:
                edges.append(e[0])
            else:
                # shouldn't happen if graph is up to date
                print('Warning: graph is missing flows')
        return edges

    def _build_formula(self, solution_part, implementation):
        question = solution_part.question
        is_absolute = solution_part.is_absolute
        a = solution_part.a
        b = solution_part.b
        q = 0

        if question:
            quantity = ImplementationQuantity.objects.get(
                question=solution_part.question,
                implementation=implementation)
            # question overrides is_absolute of part
            is_absolute = question.is_absolute
            q = quantity.value

        formula = Formula(a=a, b=b, q=q, is_absolute=is_absolute)

        return formula

    def build(self):

        base_graph = BaseGraph(self.keyflow, tag=self.tag)
        if not base_graph.exists:
            raise FileNotFoundError
        g = base_graph.load()
        gw = GraphWalker(g)

        # remove previous calc. from database
        self.clean()

        # add change attribute, it defaults to 0.0
        g.ep.change = g.new_edge_property("float")
        # add include attribute, it defaults to False
        g.ep.include = g.new_edge_property("bool")
        g.ep.changed = g.new_edge_property("bool")

        # get the solutions in this strategy and order them by priority
        solutions_in_strategy = SolutionInStrategy.objects.filter(
            strategy=self.strategy).order_by('priority')
        for implementation in solutions_in_strategy.order_by('priority'):
            solution = implementation.solution
            parts = solution.solution_parts.all()
            # get the solution parts using the reverse relation
            for solution_part in parts.order_by('priority'):
                deltas = []
                formula = self._build_formula(
                    solution_part, implementation)

                if solution_part.scheme == Scheme.MODIFICATION:
                    reference = solution_part.flow_reference
                    implementation_flows = self._get_referenced_flows(
                        reference, implementation)
                    for flow in implementation_flows:
                        delta = formula.calculate_delta(flow.amount)
                        if formula.is_absolute:
                            # equal distribution or distribution depending on
                            # previous share on total amount?
                            delta /= len(implementation_flows)
                            # alternatively sth like that
                            # delta *= flow.amount / total
                        deltas.append(delta)
                else:
                    continue # only mod implemented for now

                #if solution_part.scheme == Scheme.SHIFTDESTINATION:
                    #target_activity = solution_part.new_target_activity
                    #keep_origin = solution_part.keep_origin
                    ## ToDo: remove picking, ActorInSolutionPart already removed
                    #target_actor = Actor.objects.first()
                    ## the new flows will be the ones affected by
                    ## calculation first
                    #implementation_flows = self.create_new_flows(
                        #implementation_flows, target_actor,
                        #g, formula, keep_origin=keep_origin)

                affected_flows = self._get_affected_flows(solution_part)
                # exclude all edges
                self._reset_include(g, do_include=False)
                # include affected flows
                self._include(g, affected_flows)
                # exclude implementation flows (ToDo: side effects?)
                self._include(g, implementation_flows, do_include=False)

                impl_edges = self._get_edges(g, implementation_flows)

                # ToDo: SolutionInStrategy geometry for filtering?
                gw = GraphWalker(g)
                g = gw.calculate(impl_edges, deltas)

        self.graph = g
        # save the strategy graph to a file
        self.graph.save(self.filename)

        # save modifications and new flows into database
        self.translate_to_db()
        return self.graph

    def translate_to_db(self):
        # ToDo: filter for changes
        # store edges (flows) to database
        strat_flows = []
        changed_edges = util.find_edge(
            self.graph, self.graph.ep['changed'], True)
        for edge in changed_edges:
            new_amount = self.graph.ep.amount[edge]
            # get the related FractionFlow
            flow = FractionFlow.objects.get(id=self.graph.ep.id[edge])
            # new flow is marked with strategy relation
            # (no seperate strategy fraction flow needed)
            if flow.strategy is not None:
                flow.amount = new_amount
                flow.save()
            # changed flow gets a related strategy fraction flow holding changes
            else:
                # ToDo: get material from graph
                strat_flow = StrategyFractionFlow(
                    strategy=self.strategy, amount=new_amount,
                    fractionflow=flow,
                    material_id=flow.material.id)
                strat_flows.append(strat_flow)

        StrategyFractionFlow.objects.bulk_create(strat_flows)

try:
    import graph_tool as gt
    from graph_tool import stats as gt_stats
    from graph_tool import draw, util
    import cairo
except ModuleNotFoundError:
    pass

from django.db.models import Q, Sum, F
from django.db.models.functions import Coalesce
from django.db import connection
import numpy as np
import pandas as pd
import datetime
from io import StringIO
from django.conf import settings
import os
from datetime import datetime
from itertools import chain
import itertools
import time

from repair.apps.asmfa.models import (Actor2Actor, FractionFlow, Actor,
                                      ActorStock, Material,
                                      StrategyFractionFlow)
from repair.apps.changes.models import (SolutionInStrategy,
                                        ImplementationQuantity,
                                        AffectedFlow, Scheme,
                                        ImplementationArea)
from repair.apps.statusquo.models import SpatialChoice
from repair.apps.utils.utils import descend_materials, copy_django_model
from repair.apps.asmfa.graphs.graphwalker import GraphWalker


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
        if solution_part.scheme == Scheme.NEW and not is_absolute:
            raise ValueError('new flows without reference can only be defined '
                             'as absolute changes')
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
        return self.calculate_delta(v) + v

    def calculate_delta(self, v=None):
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
        if self.is_absolute:
            delta = self.a * self.q + self.b
        else:
            if v is None:
                raise ValueError('Value needed for calculation the delta for '
                                 'relative changes')
            delta = v * self.calculate_factor(v) - v
        return delta

    def calculate_factor(self, v):
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
            delta = self.calculate_delta()
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
        self.graph.vertex_properties["downstream_balance_factor"] = \
            self.graph.new_vertex_property("double", val=1)

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
        self.graph.edge_properties['waste'] = \
            self.graph.new_edge_property("bool")
        self.graph.edge_properties['hazardous'] = \
            self.graph.new_edge_property("bool")

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

        #  get the original order of the vertices and edges in the graph
        edge_index = np.fromiter(self.graph.edge_index,  dtype=int)
        vertex_index = np.fromiter(self.graph.vertex_index,  dtype=int)
        # get an array with the source and target ids of all edges
        edges = self.graph.get_edges()
        # get the amounts, sorted by the edge_index
        amount = self.graph.ep.amount.a[edge_index]

        #  put them in a Dataframe
        df = pd.DataFrame(data={'amount': amount,
                                'fromnode': edges[:, 0],
                                'tonode': edges[: ,1],})

        # sum up the in- and outflows for each node
        sum_fromnode = df.groupby('fromnode').sum()
        sum_fromnode.index.name = 'nodeid'
        sum_fromnode.rename(columns={'amount': 'sum_outflows',}, inplace=True)
        sum_tonode = df.groupby('tonode').sum()
        sum_tonode.index.name = 'nodeid'
        sum_tonode.rename(columns={'amount': 'sum_inflows',}, inplace=True)

        # merge in- and outflows
        merged = sum_tonode.merge(sum_fromnode, how='outer',  on='nodeid')
        # calculate the balance_factor
        merged['balance_factor'] = merged['sum_outflows'] / merged['sum_inflows']
        #  set balance_factor to 1.0, if inflow or outflow is NAN
        balance_factor = merged['balance_factor'].fillna(value=1).sort_index()

        #  set balance_factor also to 1.0 if it is 0 or infinitive
        balance_factor.loc[balance_factor==0] = 1
        balance_factor.loc[np.isinf(balance_factor)] = 1

        #  write the results to the property-map downstream_balance_factor
        self.graph.vp.downstream_balance_factor.a[vertex_index] = balance_factor

        self.save()
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

    def _modify_flows(self, flows, formula, new_material=None, new_process=None,
                      new_waste=-1, new_hazardous=-1):
        '''
        modify flows with formula
        '''
        deltas = []
        if (new_material or new_process or
            new_waste >= 0 or new_hazardous >= 0):
            edges = self._get_edges(flows)
        for i, flow in enumerate(flows):
            delta = formula.calculate_delta(flow.amount)
            if formula.is_absolute:
                # equal distribution or distribution depending on
                # previous share on total amount?
                delta /= len(flows)
                # alternatively sth like that: delta *= flow.amount / total
            deltas.append(delta)
            if new_material:
                self.graph.ep.material[edges[i]] = new_material.id
            if new_process:
                self.graph.ep.process[edges[i]] = new_process.id
            if new_waste >= 0:
                self.graph.ep.waste[edges[i]] = new_waste == 1
            if new_hazardous >= 0:
                self.graph.ep.hazardous[edges[i]] = new_hazardous == 1
        return deltas

    def _create_flows(self, origins, destinations, material, process, formula):
        '''
        create flows between all origin and destination actors
        '''
        total = formula.calculate_delta()
        flow_count = len(origins) * len(destinations)
        # equal distribution
        amount = total / flow_count
        deltas = np.full((flow_count), amount)
        new_flows = []
        for origin, destination in itertools.product(origins, destinations):
            new_flow = FractionFlow(
                origin=origin, destination=destination,
                material=material, process=process,
                amount=0,
                strategy=self.strategy,
                keyflow=self.keyflow
            )
            #new_flows.append(new_flow)
            # spatialite doesn't set the ids when bulk creating
            # when saving it does (weird)
            new_flow.save()
            o_vertex = self._get_vertex(origin.id)
            d_vertex = self._get_vertex(destination.id)
            new_edge = self.graph.add_edge(o_vertex, d_vertex)
            self.graph.ep.id[new_edge] = new_flow.id
            self.graph.ep.amount[new_edge] = 0
            self.graph.ep.material[new_edge] = new_flow.material.id
            self.graph.ep.process[new_edge] = \
                new_flow.process.id if new_flow.process is not None else - 1
            new_flows.append(new_flow)

        #FractionFlow.objects.bulk_create(new_flows)
        return new_flows, deltas

    def _shift_flows(self, referenced_flows, possible_new_targets,
                     formula, new_material=None, new_process=None,
                     shift_origin=True, reduce_reference=True,
                     new_waste=-1, new_hazardous=-1):
        '''
        creates new flows based on given referenced flows and redirects them
        to target actor (either origin or destinations are changing)

        referenced_flows are reduced by amout of new flows if reduce_reference
        is True, otherwise they stay untouched

        returns flows to be changed in order of change and the deltas added to
        be to each flow in walker algorithm in same order as flows
        '''
        changed_ref_flows = []
        new_flows = []
        changed_ref_deltas = []
        new_deltas = []

        # the actors to keep (not shifted)
        ids = referenced_flows.values_list('destination') if shift_origin\
            else referenced_flows.values_list('origin')
        actors_kept = Actor.objects.filter(id__in=ids)

        # actors in possible new targets that are closest
        closest_dict = self.find_closest_actor(actors_kept,
                                             possible_new_targets)

        # create new flows and add corresponding edges
        for flow in referenced_flows:
            kept_id = flow.destination_id if shift_origin \
                else flow.origin_id

            # no target actor found within range
            if kept_id not in closest_dict:
                continue

            # get new target out of dictionary
            new_id = closest_dict[kept_id]

            new_vertex = self._get_vertex(new_id)

            delta = formula.calculate_delta(flow.s_amount)
            # ToDo: distribute total change to changes on edges
            # depending on share of total or distribute equally?
            if formula.is_absolute:
                # equally
                delta /= len(referenced_flows)
            delta = flow.s_amount + delta

            # the edge corresponding to the referenced flow
            # (the one to be shifted)
            edges = util.find_edge(self.graph, self.graph.ep['id'], flow.id)
            if len(edges) > 1:
                raise ValueError("FractionFlow.id ", flow.id,
                                 " is not unique in the graph")
            elif len(edges) == 0:
                print("Cannot find FractionFlow.id ", flow.id, " in the graph")
                continue
            edge = edges[0]

            new_edge_args = [new_vertex, edge.target()] if shift_origin \
                else [edge.source(), new_vertex]
            new_edge = self.graph.edge(*new_edge_args)

            # create a new fractionflow for the implementation flow in db,
            # setting id to None creates new one when saving
            # while keeping attributes of original model;
            # the new flow is added with zero amount and to be changed
            # by calculated delta
            new_flow = copy_django_model(flow)
            new_flow.id = None
            new_flow.amount = 0
            if shift_origin:
                new_flow.origin_id = new_id
            else:
                new_flow.destination_id = new_id
            if new_material:
                new_flow.material = new_material
            if new_process:
                new_flow.process = new_process
            if new_waste >= 0:
                new_flow.waste = new_waste == 1
            if new_hazardous >= 0:
                new_flow.hazardous = new_hazardous == 1

            # strategy marks flow as new flow
            new_flow.strategy = self.strategy
            new_flow.save()

            # create the edge in the graph
            new_edge = self.graph.add_edge(*new_edge_args)
            self.graph.ep.id[new_edge] = new_flow.id
            self.graph.ep.amount[new_edge] = 0

            self.graph.ep.material[new_edge] = new_flow.material.id
            # process doesn't have to be set, missing attributes
            # are marked with -1 in graph (if i remember correctly?)
            self.graph.ep.process[new_edge] = \
                new_flow.process.id if new_flow.process is not None else - 1
            self.graph.ep.waste[new_edge] = new_flow.waste
            self.graph.ep.hazardous[new_edge] = new_flow.hazardous

            new_flows.append(new_flow)
            new_deltas.append(delta)

            # reduce (resp. increase) the referenced flow by the same amount
            if reduce_reference:
                changed_ref_flows.append(flow)
                changed_ref_deltas.append(-delta)

        # new flows shall be created before modifying the existing ones
        return new_flows + changed_ref_flows, new_deltas + changed_ref_deltas


    def _chain_flows(self, referenced_flows, possible_new_targets,
                     formula, new_material=None, new_process=None,
                     prepend=True, new_waste=-1, new_hazardous=-1):
        '''
        creates new flows based on given referenced flows and prepends
        (prepend==True) or appends (prepend==False) them

        if new flows already exist, changes existing ones instead

        returns new/changed flows and deltas in same order as flows

        ToDo: almost the same as shift_flows(), generalize!
        '''
        new_flows = []
        deltas = []

        ids = referenced_flows.values_list('destination') if prepend\
            else referenced_flows.values_list('origin')
        actors_kept = Actor.objects.filter(id__in=ids)

        closest_dict = self.find_closest_actor(actors_kept,
                                               possible_new_targets)

        # create new flows and add corresponding edges
        for flow in referenced_flows:
            kept_id = flow.destination_id if prepend \
                else flow.origin_id

            # no target actor found within range
            if kept_id not in closest_dict:
                continue

            # get new target out of dictionary
            new_id = closest_dict[kept_id]

            new_vertex = self._get_vertex(new_id)

            delta = formula.calculate_delta(flow.s_amount)
            # ToDo: distribute total change to changes on edges
            # depending on share of total or distribute equally?
            if formula.is_absolute:
                # equally
                delta /= len(referenced_flows)

            # the edge corresponding to the referenced flow
            edges = util.find_edge(self.graph, self.graph.ep['id'], flow.id)
            if len(edges) > 1:
                raise ValueError("FractionFlow.id ", flow.id,
                                 " is not unique in the graph")
            elif len(edges) == 0:
                print("Cannot find FractionFlow.id ", flow.id, " in the graph")
                continue
            edge = edges[0]

            new_edge_args = [new_vertex, edge.source()] if prepend \
                else [edge.target(), new_vertex]
            new_edge = self.graph.edge(*new_edge_args)

            # create a new fractionflow for the implementation flow in db,
            # setting id to None creates new one when saving
            # while keeping attributes of original model;
            # the new flow is added with zero amount and to be changed
            # by calculated delta
            new_flow = copy_django_model(flow)
            new_flow.id = None
            new_flow.amount = 0
            if prepend:
                new_flow.destination_id = new_flow.origin_id
                new_flow.origin_id = new_id
            else:
                new_flow.origin_id = new_flow.destination_id
                new_flow.destination_id = new_id
            if new_material:
                new_flow.material = new_material
            if new_process:
                new_flow.process = new_process
            if new_waste >= 0:
                new_flow.waste = new_waste == 1
            if new_hazardous >= 0:
                new_flow.hazardous = new_hazardous == 1

            # strategy marks flow as new flow
            new_flow.strategy = self.strategy
            new_flow.save()

            # create the edge in the graph
            new_edge = self.graph.add_edge(*new_edge_args)
            self.graph.ep.id[new_edge] = new_flow.id
            self.graph.ep.amount[new_edge] = 0

            self.graph.ep.material[new_edge] = new_flow.material.id
            # process doesn't have to be set, missing attributes
            # are marked with -1 in graph (if i remember correctly?)
            self.graph.ep.process[new_edge] = \
                new_flow.process.id if new_flow.process is not None else - 1
            self.graph.ep.waste[new_edge] = new_flow.waste
            self.graph.ep.hazardous[new_edge] = new_flow.hazardous

            new_flows.append(new_flow)
            deltas.append(flow.s_amount + delta)

        return new_flows, deltas

    def clean_db(self):
        '''
        wipe all related StrategyFractionFlows
        and related new FractionFlows from database
        '''
        new_flows = FractionFlow.objects.filter(strategy=self.strategy)
        new_flows.delete()
        modified = StrategyFractionFlow.objects.filter(strategy=self.strategy)
        modified.delete()

    def _get_actors(self, flow_reference, implementation):
        origins = destinations = []
        if flow_reference.origin_activity:
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
        if flow_reference.destination_activity:
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
        return origins, destinations

    def _get_referenced_flows(self, flow_reference, implementation):
        '''
        return flows on actor level filtered by flow_reference attributes
        and implementation areas
        '''
        #impl_materials = descend_materials(
            #[flow_reference.material])
        origins, destinations = self._get_actors(flow_reference, implementation)
        flows = FractionFlow.objects.filter(
            origin__in=origins,
            destination__in=destinations
        )
        flows = self._annotate(flows)
        kwargs = {
            's_material': flow_reference.material.id
        }
        if flow_reference.process:
            kwargs['s_process'] = flow_reference.process
        reference_flows = flows.filter(**kwargs)
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
        aff_flows = FractionFlow.objects.none()
        for af in affectedflows:
            #materials = descend_materials([af.material])
            flows = FractionFlow.objects.filter(
                origin__activity = af.origin_activity,
                destination__activity = af.destination_activity
            )
            flows = self._annotate(flows)
            kwargs = {
                's_material': af.material.id
            }
            if af.process:
                kwargs['s_process': af.process]
            aff_flows = aff_flows | flows.filter(**kwargs)
        return aff_flows

    def _annotate(self, flows):
        ''' annotate flows with strategy attributes (trailing "s_") '''
        annotated = flows.annotate(
            s_amount=Coalesce('f_strategyfractionflow__amount', 'amount'),
            s_material=Coalesce('f_strategyfractionflow__material', 'material'),
            s_waste=Coalesce('f_strategyfractionflow__waste', 'waste'),
            s_hazardous=Coalesce('f_strategyfractionflow__hazardous',
                                 'hazardous'),
            s_process=Coalesce('f_strategyfractionflow__hazardous',
                                 'hazardous')
        )
        return annotated

    def _include(self, flows, do_include=True):
        '''
        include flows in graph, excludes all others
        set do_include=False to exclude
        graph is changed in place
        '''
        start = time.time()
        # include affected edges
        edges = self._get_edges(flows)
        for edge in edges:
            self.graph.ep.include[edge] = do_include
        end = time.time()

    def _reset_include(self, do_include=True):
        # exclude all
        self.graph.ep.include.a[:] = do_include

    def _get_edges(self, flows):
        edges = []
        for flow in flows:
            e = util.find_edge(self.graph, self.graph.ep['id'], flow.id)
            if len(e) > 0:
                edges.append(e[0])
            else:
                # shouldn't happen if graph is up to date
                raise Exception(f'graph is missing flow {flow.id}')
        return edges

    def _get_vertex(self, id):
        ''' return vertex with given id, creates vertex with corresponding
        actor information if id is not in graph yet'''
        vertices = util.find_vertex(
            self.graph, self.graph.vp['id'], id)

        if(len(vertices) > 0):
            return vertices[0]

        # add actor to graph
        actor = Actor.objects.get(id=id)
        vertex = self.graph.add_vertex()
        # not existing in basegraph -> no flows in or out in status quo ->
        # balance factor of 1
        self.graph.vp.downstream_balance_factor[vertex] = 1
        self.graph.vp.id[vertex] = id
        self.graph.vp.bvdid[vertex] = actor.BvDid
        self.graph.vp.name[vertex] = actor.name
        return vertex

    def build(self):
        base_graph = BaseGraph(self.keyflow, tag=self.tag)
        # if the base graph is not built yet, it shouldn't be done automatically
        # there are permissions controlling who is allowed to build it and
        # who isn't
        if not base_graph.exists:
            raise FileNotFoundError
        self.graph = base_graph.load()
        gw = GraphWalker(self.graph)
        self.clean_db()
        #self.mock_changes()
        #return

        # attribute marks edges to be ignored or not (defaults to False)
        self.graph.ep.include = self.graph.new_edge_property("bool")
        # attribute marks changed edges (defaults to False)
        self.graph.ep.changed = self.graph.new_edge_property("bool")

        # get the implementations of the solution in this strategy
        # and order them by priority
        # wording might confuse (implementation instead of solution in strategy)
        # but we shifted to using the term "implementation" in most parts
        implementations = SolutionInStrategy.objects.filter(
                strategy=self.strategy).order_by('priority')
        for implementation in implementations.order_by('priority'):
            solution = implementation.solution
            parts = solution.solution_parts.all()
            # get the solution parts using the reverse relation
            for solution_part in parts.order_by('priority'):
                deltas = []
                formula = Formula.from_implementation(
                    solution_part, implementation)

                # all but new flows reference existing flows (there the
                # implementation flows are the new ones themselves)
                reference = solution_part.flow_reference
                changes = solution_part.flow_changes
                if solution_part.scheme != Scheme.NEW:
                    implementation_flows = self._get_referenced_flows(
                        reference, implementation)

                if solution_part.scheme == Scheme.MODIFICATION:
                    kwargs = {}
                    if changes:
                        kwargs['new_material'] = changes.material
                        kwargs['new_process'] = changes.process
                        kwargs['new_waste'] = changes.waste
                        kwargs['new_hazardous'] = changes.hazardous

                    deltas = self._modify_flows(implementation_flows, formula,
                                                **kwargs)

                elif solution_part.scheme == Scheme.SHIFTDESTINATION:
                    o, possible_destinations = self._get_actors(
                        changes, implementation)
                    implementation_flows, deltas = self._shift_flows(
                        implementation_flows, possible_destinations,
                        formula, shift_origin=False,
                        new_material=changes.material,
                        new_process=changes.process,
                        new_waste=changes.waste,
                        new_hazardous=changes.hazardous
                    )

                elif solution_part.scheme == Scheme.SHIFTORIGIN:
                    possible_origins, d = self._get_actors(
                        changes, implementation)
                    implementation_flows, deltas = self._shift_flows(
                        implementation_flows, possible_origins,
                        formula, shift_origin=True,
                        new_material=changes.material,
                        new_process=changes.process,
                        new_waste=changes.waste,
                        new_hazardous=changes.hazardous
                    )

                elif solution_part.scheme == Scheme.NEW:
                    origins, destinations = self._get_actors(
                        changes, implementation)
                    implementation_flows, deltas = self._create_flows(
                        origins, destinations, changes.material,
                        changes.process, formula)

                elif solution_part.scheme == Scheme.PREPEND:
                    possible_origins, d = self._get_actors(
                        changes, implementation)
                    if len(possible_origins) > 0:
                        implementation_flows, deltas = self._chain_flows(
                            implementation_flows, possible_origins,
                            formula, prepend=True,
                            new_material=changes.material,
                            new_process=changes.process,
                            new_waste=changes.waste,
                            new_hazardous=changes.hazardous)
                    else:
                        print('Warning: no new targets found! Skipping prepend')

                elif solution_part.scheme == Scheme.APPEND:
                    o, possible_destinations = self._get_actors(
                        changes, implementation)
                    if len(possible_destinations) > 0:
                        implementation_flows, deltas = self._chain_flows(
                            implementation_flows, possible_destinations,
                            formula, prepend=False,
                            new_material=changes.material,
                            new_process=changes.process,
                            new_waste=changes.waste,
                            new_hazardous=changes.hazardous)
                    else:
                        print('Warning: no new targets found! Skipping append')

                else:
                    raise ValueError(
                        f'scheme {solution_part.scheme} is not implemented')

                affected_flows = self._get_affected_flows(solution_part)
                # exclude all edges
                self._reset_include(do_include=False)
                # include affected flows
                self._include(affected_flows)
                # exclude implementation flows in case they are also in affected
                # flows (ToDo: side effects?)
                #self._include(implementation_flows, do_include=False)

                impl_edges = self._get_edges(implementation_flows)

                gw = GraphWalker(self.graph)
                self.graph = gw.calculate(impl_edges, deltas)

                # save modifications and new flows into database
                self.translate_to_db()
                self.graph.ep.changed.a[:] = False

        # save the strategy graph to a file
        self.graph.save(self.filename)

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
            material = self.graph.ep.material[edge]
            process = self.graph.ep.process[edge]
            if process == -1:
                process = None
            waste = self.graph.ep.waste[edge]
            hazardous = self.graph.ep.hazardous[edge]
            # new flow is marked with strategy relation
            # (no seperate strategy fraction flow needed)
            if flow.strategy is not None:
                flow.amount = new_amount
                flow.hazardous = hazardous
                flow.material_id = material
                flow.waste = waste
                flow.process_id = process
                flow.save()
            # changed flow gets a related strategy fraction flow holding changes
            else:
                ex = StrategyFractionFlow.objects.filter(
                    fractionflow=flow, strategy=self.strategy)
                # if there already was a modification, overwrite it
                if len(ex) == 1:
                    strat_flow = ex[0]
                    strat_flow.amount = new_amount
                    strat_flow.material_id = material
                    strat_flow.waste = waste
                    strat_flow.hazardous = hazardous
                    strat_flow.process_id = process
                    strat_flow.save()
                elif len(ex) > 1:
                    raise Exception('more than StrategyFractionFlow '
                                    'found per flow. This should not happen.')
                else:
                    strat_flow = StrategyFractionFlow(
                        strategy=self.strategy,
                        amount=new_amount,
                        fractionflow=flow,
                        material_id=material,
                        waste=waste,
                        hazardous=hazardous,
                        process_id=process
                    )
                    strat_flows.append(strat_flow)

        StrategyFractionFlow.objects.bulk_create(strat_flows)

    @staticmethod
    def find_closest_actor(actors_in_solution,
                           possible_target_actors,
                           max_distance: int=500,
                           absolute_max_distance: int=100000):
        # ToDo: for each actor pick a closest new one
        #     don't distribute amounts equally!
        #     (calc. amount based on the shifted flow for relative or distribute
        #      absolute total based on total amounts going into the shifted
        #      actor before?)
        backend = connection.vendor
        st_dwithin = {'sqlite': 'PtDistWithin',
                      'postgresql': 'st_dwithin',}

        cast_to_geography = {'sqlite': '',
                             'postgresql': '::geography',}

        # code for auto picking actor by distance
        # start with maximum distance of 500m
        target_actors = dict()

        actors_not_found_yet = actors_in_solution

        while (actors_not_found_yet
               and max_distance < absolute_max_distance):

            query_actors_in_solution = actors_not_found_yet \
                .annotate(pnt=F('administrative_location__geom')) \
                .values('id', 'pnt') \
                .query

            query_target_actors = possible_target_actors \
                .annotate(pnt=F('administrative_location__geom')) \
                .values('id', 'pnt') \
                .query

            if backend == 'sqlite':
                querytext_actors_in_solution,  params_actors_in_solution = \
                    query_actors_in_solution.sql_with_params()
                querytext_actors_in_solution = \
                    querytext_actors_in_solution.replace(
                        'CAST (AsEWKB("asmfa_administrativelocation"."geom") AS BLOB)',
                        '"asmfa_administrativelocation"."geom"')

                querytext_target_actors,  params_target_actors = \
                    query_target_actors.sql_with_params()
                querytext_target_actors = querytext_target_actors.replace(
                    'CAST (AsEWKB("asmfa_administrativelocation"."geom") AS BLOB)',
                    '"asmfa_administrativelocation"."geom"')

                query = f'''
                WITH
                  ais AS ({querytext_actors_in_solution}),
                  pta AS ({querytext_target_actors})
                SELECT
                  a.actor_id,
                  a.target_actor_id
                FROM
                  (SELECT
                    ais.id AS actor_id,
                    pta.id AS target_actor_id,
                    st_distance(
                        ST_Transform(ais.pnt, 3035),
                        ST_Transform(pta.pnt, 3035)) AS meter
                  FROM ais, pta
                  WHERE PtDistWithin(ais.pnt,
                                   pta.pnt,
                                   {max_distance})
                  ) a,
                  (SELECT
                    ais.id AS actor_id,
                    min(st_distance(
                        ST_Transform(ais.pnt, 3035),
                        ST_Transform(pta.pnt, 3035))) AS min_meter
                  FROM ais, pta
                  WHERE PtDistWithin(ais.pnt,
                                     pta.pnt,
                                     {max_distance})
                  GROUP BY ais.id
                  ) b
                WHERE a.actor_id = b.actor_id
                AND a.meter = b.min_meter
                '''

                params = params_actors_in_solution + params_target_actors

            elif backend == 'postgresql':
                query_actors_in_solution = str(
                    query_actors_in_solution).replace(
                    '"asmfa_administrativelocation"."geom"::bytea',
                    '"asmfa_administrativelocation"."geom"')

                query_target_actors = str(query_target_actors).replace(
                    '"asmfa_administrativelocation"."geom"::bytea',
                    '"asmfa_administrativelocation"."geom"')

                query = f'''
                WITH
                  ais AS ({query_actors_in_solution}),
                  pta AS ({query_target_actors})
                SELECT
                  a.actor_id,
                  a.target_actor_id
                FROM
                  (SELECT
                    ais.id AS actor_id,
                    pta.id AS target_actor_id,
                    row_number() OVER(
                      PARTITION BY ais.id
                      ORDER BY st_distance(
                        ST_Transform(ais.pnt, 3035), ST_Transform(pta.pnt, 3035))
                        ) AS rn
                  FROM ais, pta
                  WHERE st_dwithin(ais.pnt::geography,
                                   pta.pnt::geography,
                                   {max_distance})
                  ) a
                WHERE a.rn = 1
                '''

                params = ()

            else:
                raise ConnectionError(f'unknown backend: {backend}')


            with connection.cursor() as cursor:
                cursor.execute(query,  params)
                rows = cursor.fetchall()

            target_actors.update(dict(rows))

            actors_not_found_yet = actors_in_solution.exclude(
                id__in=target_actors.keys())

            max_distance *= 2
            max_distance = min(max_distance, absolute_max_distance)

        return target_actors

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
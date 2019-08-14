try:
    import graph_tool as gt
    from graph_tool import stats as gt_stats
    from graph_tool import draw, util
    import cairo
except ModuleNotFoundError:
    pass

from django.db.models import Q, Sum, F
from django.db import connection
import numpy as np
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
            delta = v * self.calculate_factor(v)
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

    def _modify_flows(self, flows, formula):
        '''
        modify flows with formula
        '''
        deltas = []
        for flow in flows:
            delta = formula.calculate_delta(flow.amount)
            if formula.is_absolute:
                # equal distribution or distribution depending on
                # previous share on total amount?
                delta /= len(flows)
                # alternatively sth like that: delta *= flow.amount / total
            deltas.append(delta)
        return deltas

    def _create_flows(self, origins, destinations, material, process, formula):
        '''
        create flows between all origin and destination actors
        '''
        total = formula.calculate_delta()
        flow_count = len(origins) * len(destinations)
        # equal distribution
        amount = total / flow_count
        deltas = [amount] * flow_count
        new_flows = []
        for origin, destination in itertools.product(origins, destinations):
            new_flow = FractionFlow(
                origin=origin, destination=destination,
                material=material, process=process,
                amount=0,
                strategy=self.strategy,
                keyflow=self.keyflow
            )
            new_flows.append(new_flow)
        FractionFlow.objects.bulk_create(new_flows)

        # ToDo: optimize (and/or make seperate function, almost the same
        # in shift_flows())
        for new_flow in new_flows:
            # create the edge in the graph
            o_vertex = util.find_vertex(
                self.graph, self.graph.vp['id'], origin.id)[0]
            d_vertex = util.find_vertex(
                self.graph, self.graph.vp['id'], destination.id)[0]
            new_edge = self.graph.add_edge(o_vertex, d_vertex)
            self.graph.ep.id[new_edge] = new_flow.id
            self.graph.ep.amount[new_edge] = 0
            self.graph.ep.material[new_edge] = new_flow.material.id
            self.graph.ep.process[new_edge] = \
                new_flow.process.id if new_flow.process is not None else - 1

        return new_flows, deltas

    def _shift_flows(self, referenced_flows, possible_new_targets,
                     formula, new_material=None, new_process=None,
                     shift_origin=True, reduce_reference=True):
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

        ids = referenced_flows.values_list('origin') if shift_origin\
            else referenced_flows.values_list('destination')
        actors_to_shift = Actor.objects.filter(id__in=ids)

        shift_dict = self.find_closest_actor(actors_to_shift,
                                             possible_new_targets)
        # create new flows and add corresponding edges
        for flow in referenced_flows:
            old_id = flow.origin_id if shift_origin \
                else flow.destination_id

            # no target actor found within range
            if old_id not in shift_dict:
                continue

            # get new target out of dictionary
            new_id = shift_dict[old_id]

            new_vertex = util.find_vertex(
                self.graph, self.graph.vp['id'], new_id)[0]

            delta = formula.calculate_delta(flow.amount)
            # ToDo: distribute total change to changes on edges
            # depending on share of total or distribute equally?
            if formula.is_absolute:
                # equally
                delta /= len(referenced_flows)

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

            # the edge might already exist, change this one instead of creating
            # a new one, changed material and process also require real shift
            if new_edge and not new_material and not new_process:
                # get flow from database and add to new_flows
                changed_ref_flow = Flows.get(id=new_edge.id)

                # add flow and delta to changed_ref arrays
                changed_ref_flows.append(changed_ref_flow)
                changed_ref_deltas.append(delta)
            else:
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

                new_flows.append(new_flow)
                new_deltas.append(delta)

                # reduce (resp. increase) the referenced flow by the same amount
                if reduce_reference:
                    changed_ref_flows.append(flow)
                    changed_ref_deltas.append(-delta)

        # new flows shall be created before modifying the existing ones
        return new_flows + changed_ref_flows, new_deltas + changed_ref_deltas

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

        # add change attribute, it defaults to 0.0
        self.graph.ep.change = self.graph.new_edge_property("float")
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
                    deltas = self._modify_flows(implementation_flows, formula)

                elif solution_part.scheme == Scheme.SHIFTDESTINATION:
                    o, possible_destinations = self._get_actors(
                        changes, implementation)
                    implementation_flows, deltas = self._shift_flows(
                        implementation_flows, possible_destinations,
                        formula, shift_origin=False)

                elif solution_part.scheme == Scheme.SHIFTORIGIN:
                    possible_origins, d = self._get_actors(
                        changes, implementation)
                    implementation_flows, deltas = self._shift_flows(
                        implementation_flows, possible_origins,
                        formula, shift_origin=True)

                elif solution_part.scheme == Scheme.NEW:
                    origins, destinations = self._get_actors(
                        changes, implementation)
                    implementation_flows, deltas = self._create_flows(
                        origins, destinations, changes.material,
                        changes.process, formula)

                else:
                    raise ValueError(
                        f'scheme {solution_part.scheme} is not implemented')

                affected_flows = self._get_affected_flows(solution_part)
                # exclude all edges
                self._reset_include(do_include=False)
                # include affected flows
                self._include(affected_flows)
                # exclude implementation flows (ToDo: side effects?)
                self._include(implementation_flows, do_include=False)

                impl_edges = self._get_edges(implementation_flows)

                gw = GraphWalker(self.graph)
                self.graph = gw.calculate(impl_edges, deltas)

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

    @staticmethod
    def find_closest_actor(actors_in_solution,
                           possible_target_actors):
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
        max_distance = 500
        ABSOLUTE_MAX_DISTANCE = 100000
        target_actors = dict()

        actors_not_found_yet = actors_in_solution

        while (actors_not_found_yet
               and max_distance <= ABSOLUTE_MAX_DISTANCE):

            query_actors_in_solution = str(actors_not_found_yet
                .annotate(pnt=F('administrative_location__geom'))
                .values('id', 'pnt')
                .query)

            query_target_actors = str(
                possible_target_actors
                .annotate(pnt=F('administrative_location__geom'))
                .values('id', 'pnt')
                .query)

            if backend == 'sqlite':
                query_actors_in_solution = query_actors_in_solution.replace(
                    'CAST (AsEWKB("asmfa_administrativelocation"."geom") AS BLOB)',
                    '"asmfa_administrativelocation"."geom"')

                query_target_actors = query_target_actors.replace(
                    'CAST (AsEWKB("asmfa_administrativelocation"."geom") AS BLOB)',
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

            elif backend == 'postgresql':
                query_actors_in_solution = query_actors_in_solution.replace(
                    '"asmfa_administrativelocation"."geom"::bytea',
                    '"asmfa_administrativelocation"."geom"')

                query_target_actors = query_target_actors.replace(
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

            else:
                raise ConnectionError(f'unknown backend: {backend}')


            with connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
            target_actors.update(dict(rows))

            actors_not_found_yet = actors_in_solution.exclude(
                id__in=target_actors.keys())

            max_distance *= 2

        return target_actors
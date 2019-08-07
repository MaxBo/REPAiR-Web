from repair.apps.asmfa.models import (Actor2Actor, FractionFlow, Actor,
                                      ActorStock, Material,
                                      StrategyFractionFlow)
from repair.apps.changes.models import (SolutionInStrategy,
                                        ImplementationQuantity,
                                        AffectedFlow, ActorInSolutionPart)
from repair.apps.statusquo.models import SpatialChoice
from repair.apps.utils.utils import descend_materials, copy_django_model
from repair.apps.asmfa.graphs.graphwalker import GraphWalker
try:
    import graph_tool as gt
    from graph_tool import stats as gt_stats
    from graph_tool import draw, util
    import cairo
except ModuleNotFoundError:
    pass

from django.db import transaction
from django.db.models import Q, Sum, OuterRef, Subquery, Window
from django.contrib.gis.measure import D
from django.db.models.functions import Rank
from django.contrib.gis.db.models.functions import Distance
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

    @staticmethod
    def find_closest_actor(actors_in_solution,
                           possible_target_actors):
        # ToDo: for each actor pick a closest new one
        #     don't distribute amounts equally!
        #     (calc. amount based on the shifted flow for relative or distribute
        #      absolute total based on total amounts going into the shifted
        #      actor before?)
        from django.db.models import F

        from django.db import connection
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

    def shift_flows(self,
                    referenced_flows,
                    implementation_area,
                    formula,
                    target_activity,
                    material=None,
                    keep_origin=True,
                    reduce_reference=True):
        '''
        creates new flows based on given implementation flows and redirects them
        to target actor (either origin or destinations are changing)
        implementation_flows stay untouched
        graph is updated in place
        Warning: side effects on implementation_flows
        factors in place

        returns flows to be changed in order of change and the deltas added to
        be to each flow in walker algorithm in same order as flows
        '''
        changed_ref_flows = []
        new_flows = []
        changed_ref_deltas = []
        new_deltas = []
        
        actors_stay_same = []
        # collect all actors that do not change to find the new targets for
        for flow in referenced_flows:
            if keep_origin:
                actors_stay_same.append(flow.origin.id)
            else:
                actors_stay_same.append(flow.destination.id)       
        actors_in_solution = Actor.objects.filter(id__in=actors_stay_same)                                 
        
        possible_target_actors = Actor.objects.filter(activity=target_activity)
        # filter possible_target_actors by implementation_area
        for geom in implementation_area:
            possible_target_actors = possible_target_actors.filter(
                administrative_location__geom__intersects=geom)
        
        target_actors = self.find_closest_actor(actors_in_solution,
                                               possible_target_actors)
        # create new flows and add corresponding edges
        for flow in referenced_flows:
            # get new target out of dictionary, key is either origin id
            # or dest id, depending on keep_origin
            # skip if no new target found
            if keep_origin:
                # find target_actor by origin
                target_id = target_actors[flow.origin.id]
            else:
                # find target_actor by destination
                target_id = target_actors[flow.destination.id]
            target_actor = Actor.get(id=target_id)
            # no target actor found within range
            if target_actor == None:
                continue

            # check if target is already in the graph, if not create it
            target_vertex = util.find_vertex(self.graph, self.graph.vp['id'],
                                             target_actor.id)

            delta = formula.calculate_delta(flow.amount)
            # ToDo: distribute total change to changes on edges
            # depending on share of total or distribute equally?
            if formula.is_absolute:
                # equally
                delta /= len(referenced_flows)

            # Change flow in the graph
            edges = util.find_edge(self.graph, self.graph.ep['id'], flow.id)
            if len(edges) > 1:
                raise ValueError("FractionFlow.id ", flow.id,
                                 " is not unique in the graph")
            elif len(edges) == 0:
                print("Cannot find FractionFlow.id ", flow.id, " in the graph")
                continue
            edge = edges[0]

            existing_edge = True
            if keep_origin:
                # find existing edge, else create new
                new_edge = self.graph.edge(edge.source(), target_vertex)
                if new_edge == None:
                    existing_edge = False
                    new_edge = self.graph.add_edge(edge.source(), target_vertex)
            else:
                # find existing edge, else create new
                new_edge = self.graph.edge(target_vertex, edge.target())
                if new_edge == None:
                    existing_edge = False
                    new_edge = self.graph.add_edge(target_vertex, edge.target())

            if existing_edge:
                # get flow from database and add to new_flows
                changed_ref_flow = Flows.get(id=new_edge.id)

                # add flow and delta to changed_ref arrays
                changed_ref_flows.append(changed_ref_flow)
                changed_ref_deltas.append(delta)
            else:
                # create a new fractionflow for the implementation flow in the db,
                # setting id to None creates new one when saving
                # while keeping attributes of original model;
                # the new flow is added with zero amount and to be changed
                # by calculated delta
                new_flow = copy_django_model(flow)
                new_flow.id = None
                new_flow.amount = 0
                if keep_origin:
                    new_flow.destination = target_actor
                else:
                    new_flow.origin = target_actor
                # strategy marks flow as new flow
                new_flow.strategy = self.strategy
                new_flow.save()

                # create the edge in the graph
                self.graph.ep.id[new_edge] = new_flow.id
                self.graph.ep.amount[new_edge] = 0

                # ToDo: swap material
                self.graph.ep.material[new_edge] = new_flow.material.id
                self.graph.ep.process[new_edge] = \
                    new_flow.process.id if new_flow.process is not None else - 1

                new_flows.append(new_flow)
                new_deltas.append(delta)

            # reduce (resp. increase) the referenced flow by the same amount
            if reduce_reference:
                changed_ref_flows.append(flow)
                changed_ref_deltas.append(-delta)

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

    def _get_flows(self, solution_part, implementation):
        '''
        filters flows by definitions in solution part
        return tuple (implementation flows, affected flows)
        '''
        # set the AffectedFlow include property to true
        affectedflows = AffectedFlow.objects.filter(
                        solution_part=solution_part)
        solution = solution_part.solution
        # if no area is drawn by user take possible area
        implementation_area = (
            implementation.geom or
            solution.possible_implementation_area
        )
        # get FractionFlows related to AffectedFlow
        affected_flows = FractionFlow.objects.none()
        for af in affectedflows:
            # ToDo: descend materials if requested
            #materials = descend_materials([af.material])
            material = af.material
            affected_flows = \
                affected_flows | FractionFlow.objects.filter(
                    origin__activity=af.origin_activity,
                    destination__activity=af.destination_activity,
                    material=material
                    #material__in=materials
                )
        # ToDo: descend materials if requested
        #impl_materials = descend_materials(
            #[solution_part.implementation_flow_material])
        impl_material = solution_part.implementation_flow_material
        # there might be no implementation area defined for the solution
        origins = Actor.objects.filter(
            activity=solution_part.implementation_flow_origin_activity)
        destinations = Actor.objects.filter(
            activity=solution_part.implementation_flow_destination_activity)
        # filter actors by implementation geometry
        if implementation_area:
            spatial_choice = \
                solution_part.implementation_flow_spatial_application
            # iterate collection
            for geom in implementation_area:
                if spatial_choice in [SpatialChoice.BOTH, SpatialChoice.ORIGIN]:
                    origins = origins.filter(
                        administrative_location__geom__intersects=geom)
                if spatial_choice in [SpatialChoice.BOTH,
                                      SpatialChoice.DESTINATION]:
                    destinations = destinations.filter(
                        administrative_location__geom__intersects=geom)
        implementation_flows = FractionFlow.objects.filter(
            origin__in=origins,
            destination__in=destinations,
            material=impl_material
        )

        return implementation_flows, affected_flows

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
                raise Exception(f'graph is missing flow {flow.name}')
        return edges

    def build(self):
        base_graph = BaseGraph(self.keyflow, tag=self.tag)
        if not base_graph.exists:
            base_graph.build()

        # reset to base graph and remove previous calc. from database
        self.graph = base_graph.load()
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
                formula = Formula.from_implementation(
                    solution_part, implementation)

                implementation_flows, affected_flows = \
                    self._get_flows(solution_part, implementation)

                # shift flows
                if solution_part.implements_new_flow:
                    target_activity = solution_part.new_target_activity
                    keep_origin = solution_part.keep_origin
                    implementation_area = implementation.geom
                    
                    implementation_flows, deltas = self.shift_flows(
                        implementation_flows,
                        implementation_area,
                        formula,
                        target_activity,
                        keep_origin=keep_origin,
                        reduce_reference=True)
                else:
                    #total = implementation_flows.aggregate(
                        #total=Sum('amount'))['total']
                    for flow in implementation_flows:
                        delta = formula.calculate_delta(flow.amount)
                        if formula.is_absolute:
                            # equal distribution or distribution depending on
                            # previous share on total amount?
                            delta /= len(implementation_flows)
                            # alternatively sth like that
                            # delta *= flow.amount / total
                        deltas.append(delta)

                # exclude all edges
                self._reset_include(do_include=False)
                # include affected flows
                self._include(affected_flows)
                # exclude implementation flows (ToDo: side effects?)
                self._include(implementation_flows, do_include=False)

                # ToDo: how to include previous chained flows??? might not be
                # selected as affected in frontend because they don't exist in
                # status quo

                impl_edges = self._get_edges(implementation_flows)

                gw = GraphWalker(self.graph)
                self.graph = gw.calculate(impl_edges, deltas)

        # save the strategy graph to a file
        self.graph.save(self.filename)

        # save modifications and new flows into database
        self.translate_to_db()
        return self.graph

    def translate_to_db(self):
        changed = self.graph.ep['changed'].a
        ids = self.graph.ep['id'].a[changed]
        amounts = self.graph.ep['amount'].a[changed]
        flows = FractionFlow.objects.filter(id__in=ids)
        flows_list = list(flows)
        ids_flows = np.array(flows.values_list('id', flat=True))
        idx_flows = ids_flows.searchsorted(ids).tolist()

        start = time.time()

        strat_flows = []
        mod_flows = []
        for i, idx_flow in enumerate(idx_flows):
            flow = flows_list[idx_flow]
            new_amount = amounts[i]
            if flow.strategy is None:
                flow.amount = new_amount
                mod_flows.append(flow)
            else:
                strat_flow = StrategyFractionFlow(
                    strategy=self.strategy, amount=new_amount,
                    fractionflow=flow,
                    material_id=flow.material.id)
                strat_flows.append(strat_flow)

        StrategyFractionFlow.objects.bulk_create(strat_flows)
        FractionFlow.objects.bulk_update(mod_flows, ['amount'])

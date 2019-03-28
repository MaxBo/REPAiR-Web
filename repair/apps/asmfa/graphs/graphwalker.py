import graph_tool as gt
from graph_tool import util
import copy
import numpy as np
from django.db.models import Q

from repair.apps.asmfa.models.flows import FractionFlow
from repair.apps.asmfa.models import Actor
from repair.apps.changes.factories import StrategyFractionFlowFactory

class GraphWalker:
    def __init__(self, G):
        self.graph = gt.Graph(G)
        self.edge_mask = self.graph.new_edge_property("bool")

    def shift_flows(self, solution_object, solution_part, keyflow):
        """Shift the flows if necessary in each SolutionPart

        BD: this is just a hack hardcoded for the bread to beer case to test
        if the whole flow computation works. The SolutionPart shouldn't be
        passed as a parameter but retrieved from the DB, using the solution_object
        """
        print(solution_object.name)
        # solution_parts = SolutionPart.objects.filter(solution=solution_object)

        # BD: this should be done for each SolutionPart and then return the
        # altered graph (only one graph per solution!)
        if solution_part.implements_new_flow:
            # SolutionPart implementing new flow
            g = copy.deepcopy(self.graph)
            actors_origin = Actor.objects.filter(activity=solution_part.implementation_flow_origin_activity)
            actors_destination = Actor.objects.filter(activity=solution_part.implementation_flow_destination_activity)
            actorflows = FractionFlow.objects.filter(
                Q(origin__in=actors_origin.values('id')) &
                Q(destination__in=actors_destination.values('id')),
                material=solution_part.implementation_flow_material)
            if solution_part.keep_origin:
                # keeping origin of flow
                new_destinations = Actor.objects.filter(
                    activity=solution_part.new_target_activity)
                destinations = []
                for actor in new_destinations:
                    destinations += util.find_vertex(g, g.vp['id'], actor.id)

                for flow in actorflows:
                    x = util.find_edge(g, g.ep['id'], flow.id)
                    if len(x) > 1:
                        raise ValueError("FractionFlow ID", flow.id, "is not unique")
                    elif len(x) == 0:
                        print("Cannot find FractionFlow", flow.id, "in the graph")
                    else:
                        edge_del = x[0]
                        origin = edge_del.source()
                        amount_flow = g.ep.amount[edge_del]
                        amount_new = amount_flow / len(destinations)
                        for dest in destinations:
                            e = g.add_edge(origin, dest)
                            g.ep.amount[e] = amount_new
                            g.ep.material[e] = solution_part.implementation_flow_material
                        g.remove_edge(edge_del)
                                # StrategyFractionFlowFactory(strategy=solution_object.strategy,
                                #                             fractionflow=flow,
                                #                             amount=amount_new,
                                #                             origin=,
                                #                             destination=)
            return g

        else:
            return self.graph

    def filter_flows(self, solution_object):
        """Keep only the affected_flows and solution_flows in the graph"""
        if len(solution_object.solution_flows) > 0:
            assert isinstance(solution_object.solution_flows[0], tuple), "Flow must be a tuple of (edge id, material name)"
        elif len(solution_object.affected_flows) > 0:
            assert isinstance(solution_object.affected_flows[0], tuple), "Flow must be a tuple of (edge id, material name)"
        selected_flows = solution_object.affected_flows + solution_object.solution_flows
        for e in self.graph.edges():
            eid = self.graph.ep.id[e]
            mat = self.graph.ep.material[e]
            key = (eid, mat)
            if key in selected_flows:
                self.edge_mask[e] = True
            else:
                self.edge_mask[e] = False
        
    def calculate_solution(self, solution):
        """Calculate the changes on flows for a solution"""
        if isinstance(solution, int):
            solution = float(solution)
        assert isinstance(solution, float)
        g = copy.deepcopy(self.graph)
        for e in g.edges():
            if(g.ep.amount[e] != None):
                g.ep.amount[e] = g.ep.amount[e] * solution
        return g
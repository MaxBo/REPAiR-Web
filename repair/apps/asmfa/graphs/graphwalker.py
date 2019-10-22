try:
    import graph_tool as gt
    from graph_tool import search
    from graph_tool.search import BFSVisitor
except ModuleNotFoundError:
    class BFSVisitor:
        pass
import copy


class NodeVisitor(BFSVisitor):

    def __init__(self, name, amount, change,
                 balance_factor, forward=True):
        self.id = name
        self.amount = amount
        self.change = change
        self.balance_factor = balance_factor
        self.forward = forward

    def examine_vertex(self, u):
        vertex_id = int(u)
        out_degree = u.out_degree()
        if not out_degree:
            return

        bf = self.balance_factor[vertex_id]
        sum_in_deltas = u.in_degree(weight=self.change)
        balanced_delta = sum_in_deltas * bf
        sum_out_f = u.out_degree(weight=self.amount)
        if sum_out_f:
            amount_factor = balanced_delta / sum_out_f
        else:
            amount_factor = balanced_delta / out_degree

        for e_out in u.out_edges():
            amount_delta = self.amount[e_out] * amount_factor
            if self.forward:
                self.change[e_out] += amount_delta
            else:
                if abs(self.change[e_out]) < abs(amount_delta):
                    self.change[e_out] = amount_delta
                else:
                    self.change[e_out] += amount_delta


class NodeVisitorBalanceDeltas(BFSVisitor):

    def __init__(self, name, amount, change,
                 balance_factor):
        self.id = name
        self.amount = amount
        self.change = change
        self.balance_factor = balance_factor

    def examine_vertex(self, u):
        vertex_id = int(u)
        out_degree = u.out_degree()
        if not out_degree:
            return

        sum_in_deltas = u.in_degree(self.change)
        sum_out_deltas = u.out_degree(self.change)
        bf = self.balance_factor[vertex_id]
        balanced_out_deltas = sum_out_deltas / bf
        balanced_delta = sum_in_deltas - balanced_out_deltas
        if abs(balanced_delta) < 0.0000001:
            return
        sum_out_f = u.out_degree(weight=self.amount)
        if sum_out_f:
            amount_factor = balanced_delta / sum_out_f
        else:
            amount_factor = balanced_delta / out_degree
        for e_out in u.out_edges():
            amount_delta = self.amount[e_out] * amount_factor
            self.change[e_out] += amount_delta


def traverse_graph(g, edge, delta, upstream=True):
    """Traverse the graph in a breadth-first-search manner

    Parameters
    ----------
    g : the graph to explore
    edge : the starting edge, normally this is the *solution edge*
    delta : signed change in absolute value (eg. tons) on the implementation flow (delta). For example -26.0 (tons)
    upstream : The direction of traversal. When upstream is True, the graph
               is explored upstream first, otherwise downstream first.

    Returns
    -------
    Edge ProperyMap (float)
        The signed change on the edges
    """
    plot = False

    amount = g.ep.amount
    change = g.new_edge_property("float", val=0.0)
    total_change = g.new_edge_property("float", val=0.0)

    if plot:
        # prepare plotting of intermediate results
        from repair.apps.asmfa.tests import flowmodeltestdata
        flowmodeltestdata.plot_materials(g, file='materials.png')
        flowmodeltestdata.plot_amounts(g,'amounts.png', 'amount')
        g.ep.change = change

    # We are only interested in the edges that define the solution
    g.set_edge_filter(g.ep.include)
    MAX_ITERATIONS = 20
    balance_factor = g.vp.downstream_balance_factor.a

    # make a first run with the given changes to the implementation edge

    # By default we go upstream first, because 'demand dictates supply'
    if upstream:
        node = edge.source()
        g.set_reversed(True)
        balance_factor = 1 / balance_factor
    else:
        node = edge.target()
        g.set_reversed(False)

    # initialize the node-visitors
    node_visitor = NodeVisitor(g.vp["id"], amount, change,
                               balance_factor)
    node_visitor2 = NodeVisitorBalanceDeltas(g.vp["id"], amount, change,
                               balance_factor)

    node_visitor.forward = True
    total_change.a[:] = 0
    new_delta = delta
    i = 0
    change[edge] = new_delta
    # start in one direction
    search.bfs_search(g, node, node_visitor)
    change[edge] = new_delta

    if plot:
        ## Plot changes after forward run
        g.ep.change.a[:] = change.a
        flowmodeltestdata.plot_amounts(g,'plastic_deltas.png', 'change')

    node = reverse_graph(g, node_visitor, node_visitor2, edge)
    search.bfs_search(g, node, node_visitor)
    change[edge] = new_delta

    if plot:
        ## Plot changes after backward run
        g.ep.change.a[:] = change.a
        flowmodeltestdata.plot_amounts(g,'plastic_deltas.png', 'change')

    # balance out the changes
    search.bfs_search(g, node, node_visitor2)
    change[edge] = new_delta

    # add up the total changes
    total_change.a += change.a

    if plot:
        ## Plot total changes
        g.ep.change.a[:] = total_change.a
        flowmodeltestdata.plot_amounts(g,f'plastic_deltas_{i}.png', 'change')

    node = reverse_graph(g, node_visitor, node_visitor2, edge)

    if upstream:
        if node.in_degree():
            sum_f = node.in_degree(weight=total_change)
            new_delta = delta - sum_f
        else:
            new_delta = 0
    else:
        if node.out_degree():
            sum_f = node.out_degree(weight=total_change)
            new_delta = delta - sum_f
        else:
            new_delta = 0
    i += 1


    while i < MAX_ITERATIONS and abs(new_delta) > 0.00001:
        change.a[:] = 0
        change[edge] = new_delta

        # start in one direction

        search.bfs_search(g, node, node_visitor)
        change[edge] = 0

        if plot:
            ## Plot changes after forward run
            g.ep.change.a[:] = change.a
            flowmodeltestdata.plot_amounts(g,'plastic_deltas.png', 'change')


        # now go downstream, if we started upstream
        # (or upstream, if we started downstream)
        node = reverse_graph(g, node_visitor, node_visitor2, edge)
        if upstream:
            sum_f = node.out_degree(weight=total_change) + \
                node.out_degree(weight=change)
        else:
            sum_f = node.in_degree(weight=total_change) + \
                node.in_degree(weight=change)
        new_delta = delta - sum_f
        change[edge] = new_delta
        search.bfs_search(g, node, node_visitor)


        if plot:
            ## Plot changes after backward run
            g.ep.change.a[:] = change.a
            flowmodeltestdata.plot_amounts(g,'plastic_deltas.png', 'change')

        # balance out the changes
        search.bfs_search(g, node, node_visitor2)
        change[edge] = 0

        if plot:
            ## Plot changes after balancing
            g.ep.change.a[:] = change.a
            flowmodeltestdata.plot_amounts(g,'plastic_deltas.png', 'change')

        # add up the total changes
        total_change.a += change.a

        node = reverse_graph(g, node_visitor, node_visitor2, edge)

        if plot:
            ## Plot total changes
            g.ep.change.a[:] = total_change.a
            flowmodeltestdata.plot_amounts(g,f'plastic_deltas_{i}.png', 'change')

        if upstream:
            if node.in_degree():
                sum_f = node.in_degree(weight=total_change)
                new_delta = delta - sum_f
            else:
                new_delta = 0
        else:
            if node.out_degree():
                sum_f = node.out_degree(weight=total_change)
                new_delta = delta - sum_f
            else:
                new_delta = 0
        i += 1

    # finally clean up
    g.set_reversed(False)
    g.clear_filters()
    return total_change


def reverse_graph(g, node_visitor: NodeVisitor, node_visitor2, edge):
    g.set_reversed(not g.is_reversed())
    node_visitor.balance_factor = 1 / node_visitor.balance_factor
    node = edge.target() if not g.is_reversed() else edge.source()
    node_visitor.forward = not node_visitor.forward
    node_visitor2.balance_factor = 1 / node_visitor2.balance_factor
    return node


class GraphWalker:
    def __init__(self, g):
        self.graph = gt.Graph(g)

    def calculate(self, implementation_edges, deltas):
        """Calculate the changes on flows for a solution"""
        # ToDo: deepcopy might be expensive. Why do we clone here?
        # NOTE BD: initially the idea was that the this 'calculate' function
        # returns a copy of the graph with the updated amounts. Needed to return
        # an updated copy in order to compare this updated copy with the original
        # graph, so we can say what was changed by the solution.
        # For this, we need a deepcopy, otherwise the original graph would be
        # overwritten.
        # If it is OK to overwrite the amounts on the input graph because we
        # have this data in the database so we can compare the output (right?),
        # then no need to deepcopy.
        g = copy.deepcopy(self.graph)

        # store the changes for each actor to sum total in the end
        overall_changes = None

        for i, edge in enumerate(implementation_edges):

            g.ep.include[edge] = True
            solution_delta = deltas[i]
            changes = traverse_graph(g, edge=edge,
                                     delta=solution_delta)
            if overall_changes is None:
                overall_changes = changes.a
            else:
                overall_changes += changes.a
            g.ep.include[edge] = False

        if overall_changes is not None:
            g.ep.amount.a += overall_changes

            has_changed = overall_changes != 0
            g.ep.changed.a[has_changed] = True

        return g

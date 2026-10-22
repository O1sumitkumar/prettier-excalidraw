"""Stage 1 of the auto-layout series (#48): rank the children of a container.

`rank(graph, container_id)` assigns each direct child of the container a
rank: sources sit at rank 0, and every other node one more than the
longest path reaching it, so every edge points from a lower rank to a
higher one. Isolated nodes get rank 0. Cycles are broken by dropping the
back edge found last by a depth-first walk in spec order, which keeps the
result deterministic (rule 4 of the README: ties break on element order
in the spec). Regions are not laid out at this stage: ranking a container
ranks its children, with deeper elements lifted to it by
`Graph.edges_within`. Standard library only.
"""
from .graph import Graph


def _last_back_edge_index(kids, edges):
    """Index of the back edge a DFS in spec order finds last, or None.

    A back edge is one whose destination is on the current DFS stack, i.e.
    an edge that closes a cycle. Edges are walked in the order the spec
    lists them and children in the order they appear, so the answer is a
    function of the spec alone.
    """
    adj = {k: [] for k in kids}
    for i, e in enumerate(edges):
        adj[e.src].append((e.dst, i))
    ON, DONE = 1, 2
    state = {}
    last = None
    for start in kids:
        if state.get(start):
            continue
        state[start] = ON
        work = [(start, 0)]
        while work:
            u, i = work[-1]
            if i < len(adj[u]):
                work[-1] = (u, i + 1)
                v, edge_i = adj[u][i]
                if state.get(v) == ON:
                    last = edge_i
                elif not state.get(v):
                    state[v] = ON
                    work.append((v, 0))
            else:
                state[u] = DONE
                work.pop()
    return last


def rank(graph: Graph, container_id):
    """Return `{node_id: rank}` for the direct children of `container_id`.

    Sources rank 0; every other node one more than the longest path
    reaching it. `container_id` is None for the top level. Edges leaving
    the container do not count: a child is a source when nothing *inside*
    the container reaches it.
    """
    kids = list(graph.children(container_id))
    edges = list(graph.edges_within(container_id))

    # break cycles first, so the ranks are well defined
    while True:
        back = _last_back_edge_index(kids, edges)
        if back is None:
            break
        del edges[back]

    # longest-path ranks: a topological order computes each rank once all
    # its predecessors are known (the edge list is acyclic by now)
    preds = {k: [] for k in kids}
    succ = {k: [] for k in kids}
    for e in edges:
        preds[e.dst].append(e.src)
        succ[e.src].append(e.dst)
    indegree = {k: len(preds[k]) for k in kids}
    order = [k for k in kids if indegree[k] == 0]
    i = 0
    while i < len(order):
        u = order[i]
        i += 1
        for v in succ[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                order.append(v)
    if len(order) != len(kids):  # pragma: no cover - unreachable after cycle removal
        raise ValueError("cycle survived rank(): please report this spec as a bug")
    ranks = {}
    for u in order:
        ranks[u] = 1 + max(ranks[p] for p in preds[u]) if preds[u] else 0
    return ranks

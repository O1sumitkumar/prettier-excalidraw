"""Stage 2 of the auto-layout series (#49): order the nodes within each rank.

`order(graph, container_id, ranks)` takes the ranks stage 1 computed and
returns, per rank, the nodes in the order they should sit along the
cross-axis. The starting order is the spec order (README rule 4: ties
break on element order in the spec); two barycentre sweeps — down the
ranks, then up — reorder each rank by the positions of its neighbours in
the adjacent rank, and the candidate with the fewest crossings wins.
`crossings(orders, edges)` is the counting helper. Standard library only.
"""
from .graph import Graph


def crossings(orders, edges):
    """Count edge crossings, one adjacent-rank pair at a time.

    Only edges that connect rank r to rank r+1 directly are counted
    against each other: an edge skipping a rank has no defined crossing
    partner until it is bent, which is the nudge stage's job (#52).
    """
    pos = {n: (r, i) for r, ids in orders.items() for i, n in enumerate(ids)}
    by_pair = {}
    for e in edges:
        if e.src in pos and e.dst in pos and pos[e.dst][0] == pos[e.src][0] + 1:
            by_pair.setdefault(pos[e.src][0], []).append((e.src, e.dst))
    count = 0
    for pairs in by_pair.values():
        for i in range(len(pairs)):
            s1, d1 = pairs[i]
            for j in range(i + 1, len(pairs)):
                s2, d2 = pairs[j]
                if s1 == s2 or d1 == d2:
                    continue  # edges sharing an endpoint do not cross
                if (pos[s1][1] < pos[s2][1]) != (pos[d1][1] < pos[d2][1]):
                    count += 1
    return count


def _adjacent_neighbours(ranks, edges):
    """`{node: [neighbours exactly one rank away]}`, both directions."""
    nb = {}
    for e in edges:
        rs, rd = ranks.get(e.src), ranks.get(e.dst)
        if rs is None or rd is None or abs(rs - rd) != 1:
            continue
        nb.setdefault(e.src, []).append(e.dst)
        nb.setdefault(e.dst, []).append(e.src)
    return nb


def _sweep(orders, neighbours, down=True):
    """One barycentre sweep, reordering each rank from its adjacent rank.

    Down sweeps walk the ranks upwards, reading the rank above as it was
    just reordered; up sweeps walk downwards, reading the rank below. A
    node without neighbours in the adjacent rank stays where it was.
    """
    new = {r: list(ids) for r, ids in orders.items()}
    rank_list = sorted(new, reverse=not down)
    for r in rank_list:
        adj = new.get(r - 1 if down else r + 1)
        if not adj:
            continue
        index_of = {v: i for i, v in enumerate(adj)}
        scored = []
        for i, u in enumerate(new[r]):
            positions = [index_of[v] for v in neighbours.get(u, ()) if v in index_of]
            score = sum(positions) / len(positions) if positions else float(i)
            scored.append((score, i, u))
        new[r] = [u for _, _, u in sorted(scored)]
    return new


def order(graph: Graph, container_id, ranks):
    """Return `{rank: [node_ids]}` for the children of `container_id`.

    `ranks` is stage 1's `{node_id: rank}` for those children. The
    initial order is the spec order; the barycentre sweeps improve it and
    the candidate with the fewest crossings wins, the earliest candidate
    breaking ties so a sweep that does not help changes nothing.
    """
    kids = list(graph.children(container_id))
    edges = list(graph.edges_within(container_id))
    ranks = {k: ranks[k] for k in kids}

    initial = {}
    for k in kids:
        initial.setdefault(ranks[k], []).append(k)
    neighbours = _adjacent_neighbours(ranks, edges)
    down = _sweep(initial, neighbours, down=True)
    candidates = [initial, down, _sweep(down, neighbours, down=False)]
    best = min(
        (crossings(c, edges), i, c) for i, c in enumerate(candidates)
    )
    return best[2]

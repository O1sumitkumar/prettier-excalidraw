"""Tests for the auto-layout package (scripts/layout). One class per stage; stages
not yet implemented are skipped so contributors can add their class as they land."""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "prettier-excalidraw", "scripts")
sys.path.insert(0, SCRIPTS)

from layout import (  # noqa: E402
    from_spec,
    direction,
    layout,
    Graph,
    Node,
    Edge,
    rank,
    order,
    crossings,
)


def measure(it):
    """Stand-in for build.py's measurement: fixed sizes so tests are easy to reason about."""
    return it.get("w", 240), it.get("h", 70)


SPEC = {
    "layout": "lr",
    "elements": [
        {"id": "r", "type": "region", "title": "[ cluster ]", "x": 0, "y": 0, "w": 800, "h": 400},
        {"id": "inner", "type": "region", "title": "[ inner ]", "x": 40, "y": 200, "w": 400, "h": 160},
        {"id": "a", "type": "box", "label": "a", "x": 40, "y": 60},            # inside r by bounds
        {"id": "b", "type": "box", "label": "b", "x": 60, "y": 240},           # inside inner by bounds
        {"id": "c", "type": "box", "label": "c", "in": "r"},                   # explicit membership, no coords
        {"id": "d", "type": "box", "label": "d"},                              # top level, no coords
        {"id": "e", "type": "box", "label": "e", "x": 1000, "y": 0},           # top level, fixed
        {"type": "arrow", "from": "a", "to": "b", "label": "writes orders"},
        {"type": "arrow", "from": "b", "to": "d"},
        {"type": "arrow", "from": "e", "to": "r", "label": "in"},
    ],
}


class TestGraphModel(unittest.TestCase):
    def setUp(self):
        self.g = from_spec(SPEC, measure)

    def test_parents_by_bounds_membership_and_top_level(self):
        n = self.g.nodes
        self.assertEqual(n["a"].parent, "r")
        self.assertEqual(n["b"].parent, "inner", "innermost region wins")
        self.assertEqual(n["c"].parent, "r", "explicit 'in' key")
        self.assertIsNone(n["d"].parent)
        self.assertEqual(self.g.containers["inner"].parent, "r")
        self.assertEqual(set(self.g.root), {"r", "d", "e"})
        self.assertEqual(set(self.g.containers["r"].children), {"inner", "a", "c"})

    def test_fixed_and_sizes(self):
        self.assertEqual(self.g.nodes["a"].fixed, (40, 60))
        self.assertIsNone(self.g.nodes["c"].fixed)
        self.assertEqual((self.g.nodes["a"].w, self.g.nodes["a"].h), (240, 70))
        self.assertEqual(self.g.containers["r"].w, 800)

    def test_edges_and_label_widths(self):
        e = next(x for x in self.g.edges if x.src == "a" and x.dst == "b")
        self.assertAlmostEqual(e.label_w, len("writes orders") * 11 + 40)
        self.assertEqual(next(x for x in self.g.edges if x.src == "b").label_w, 0)

    def test_edges_within_lift_to_container_level(self):
        # inside r: a -> b becomes a -> inner (b is lifted to its container)
        within_r = {(e.src, e.dst) for e in self.g.edges_within("r")}
        self.assertIn(("a", "inner"), within_r)
        # at root: e -> r stays, b -> d becomes r -> d
        at_root = {(e.src, e.dst) for e in self.g.edges_within(None)}
        self.assertEqual(at_root, {("e", "r"), ("r", "d")})

    def test_direction_and_errors(self):
        self.assertEqual(direction({"elements": []}), "lr")
        with self.assertRaises(ValueError):
            direction({"layout": "diagonal", "elements": []})
        bad = {"elements": [{"id": "x", "type": "box", "label": "x", "in": "nope"}]}
        with self.assertRaises(ValueError):
            from_spec(bad, measure)
        with self.assertRaises(NotImplementedError):
            layout(SPEC, measure)


def _graph(direction="lr"):
    """An empty Graph for tests that build the model by hand."""
    return Graph(direction=direction)


def _box(g, id_):
    g.nodes[id_] = Node(id=id_, kind="box", w=240, h=70)
    g.root.append(id_)


class TestRank(unittest.TestCase):
    """Stage 1 (#48): longest-path ranks with deterministic cycle breaking."""

    def _rank(self, edges, nodes=()):
        """Rank a top-level graph with the given edges and isolated nodes."""
        g = _graph()
        for e in nodes:
            _box(g, e)
        seen = []
        for src, dst in edges:
            for e in (src, dst):
                if e not in seen:
                    seen.append(e)
                    _box(g, e)
            g.edges.append(Edge(src=src, dst=dst))
        return rank(g, None)

    def test_chain(self):
        r = self._rank((("a", "b"), ("b", "c")))
        self.assertEqual(r, {"a": 0, "b": 1, "c": 2})

    def test_diamond_dag_takes_the_longest_path(self):
        r = self._rank((("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")))
        self.assertEqual(r, {"a": 0, "b": 1, "c": 1, "d": 2})

    def test_longest_path_not_shortcut(self):
        # a -> b -> d and the shortcut a -> d: d ranks 2, not 1
        r = self._rank((("a", "b"), ("b", "d"), ("a", "d")))
        self.assertEqual(r["d"], 2)

    def test_cycle_drops_the_back_edge_found_last(self):
        # a -> b -> c -> a: the DFS finds c -> a as the back edge and drops it
        r = self._rank((("a", "b"), ("b", "c"), ("c", "a")))
        self.assertEqual(r, {"a": 0, "b": 1, "c": 2})

    def test_two_cycles_are_both_broken(self):
        # a -> b -> a and b -> c -> b: the last-seen back edges (c -> b, then
        # b -> a) are dropped, leaving the chain a -> b -> c
        r = self._rank((("a", "b"), ("b", "a"), ("b", "c"), ("c", "b")))
        self.assertEqual(r, {"a": 0, "b": 1, "c": 2})

    def test_disconnected_graph(self):
        # a -> b, then isolated c, then d -> e
        r = self._rank((("a", "b"), ("d", "e")), nodes=("c",))
        self.assertEqual(r, {"a": 0, "b": 1, "c": 0, "d": 0, "e": 1})

    def test_isolated_nodes_rank_zero(self):
        g = _graph()
        _box(g, "lonely")
        self.assertEqual(rank(g, None), {"lonely": 0})

    def test_regions_are_ignored_their_children_ranked(self):
        g = from_spec(SPEC, measure)
        # at the root, b -> d lifts to r -> d and e -> r stays: e, r, d
        self.assertEqual(rank(g, None), {"e": 0, "r": 1, "d": 2})
        # inside r, a -> b lifts to a -> inner; c is isolated
        self.assertEqual(rank(g, "r"), {"inner": 1, "a": 0, "c": 0})
        self.assertEqual(set(g.containers["r"].children), set(rank(g, "r")))

    def test_rank_is_a_function_of_the_spec_alone(self):
        # same graph twice: identical output (determinism, README rule 4)
        self.assertEqual(self._rank((("a", "b"), ("b", "c"), ("c", "a"))),
                         self._rank((("a", "b"), ("b", "c"), ("c", "a"))))


class TestOrder(unittest.TestCase):
    """Stage 2 (#49): barycentre ordering within each rank."""

    def _make(self, nodes, edges, ranks):
        """A top-level graph: nodes in spec order, then edges."""
        g = _graph()
        for n in nodes:
            _box(g, n)
        for src, dst in edges:
            g.edges.append(Edge(src=src, dst=dst))
        return g, {n: ranks[n] for n in nodes}

    def test_bipartite_naive_crosses_barycentre_does_not(self):
        # spec order puts x before y, but a feeds y and b feeds x
        g, ranks = self._make(
            ["a", "b", "x", "y"], [("a", "y"), ("b", "x")],
            {"a": 0, "b": 0, "x": 1, "y": 1},
        )
        initial = {0: ["a", "b"], 1: ["x", "y"]}
        self.assertEqual(crossings(initial, g.edges), 1)
        result = order(g, None, ranks)
        self.assertEqual(result, {0: ["a", "b"], 1: ["y", "x"]})
        self.assertEqual(crossings(result, g.edges), 0)

    def test_a_bad_initial_order_is_repaired(self):
        # rank 0 spec order is b, a while rank 1 is x, y: a feeds x and
        # b feeds y, so the initial orders cross and a sweep must repair
        # one of the two ranks (here: the sweeps align them with 0 crossings)
        g, ranks = self._make(
            ["b", "a", "x", "y"], [("a", "x"), ("b", "y")],
            {"b": 0, "a": 0, "x": 1, "y": 1},
        )
        initial = {0: ["b", "a"], 1: ["x", "y"]}
        self.assertEqual(crossings(initial, g.edges), 1)
        result = order(g, None, ranks)
        self.assertEqual(crossings(result, g.edges), 0)

    def test_spec_order_is_stable_when_no_edges(self):
        g, ranks = self._make(["n1", "n2", "n3"], [],
                                {"n1": 0, "n2": 0, "n3": 0})
        self.assertEqual(order(g, None, ranks), {0: ["n1", "n2", "n3"]})

    def test_sweeps_that_do_not_help_change_nothing(self):
        # already crossing-free: the initial order wins the tie
        g, ranks = self._make(
            ["a", "b", "x", "y"], [("a", "x"), ("b", "y")],
            {"a": 0, "b": 0, "x": 1, "y": 1},
        )
        self.assertEqual(
            order(g, None, ranks), {0: ["a", "b"], 1: ["x", "y"]}
        )

    def test_ties_break_on_spec_order(self):
        # two rank-1 nodes with the same barycentre keep their spec order
        g, ranks = self._make(
            ["a", "x", "y"], [("a", "x"), ("a", "y")],
            {"a": 0, "x": 1, "y": 1},
        )
        self.assertEqual(
            order(g, None, ranks), {0: ["a"], 1: ["x", "y"]}
        )

    def test_three_ranks_stay_consistent(self):
        # a chain a -> m -> z with a second path b -> m: no crossings, and
        # every rank keeps exactly its own nodes
        g, ranks = self._make(
            ["a", "b", "m", "z"],
            [("a", "m"), ("b", "m"), ("m", "z")],
            {"a": 0, "b": 0, "m": 1, "z": 2},
        )
        result = order(g, None, ranks)
        self.assertEqual(sorted(result), [0, 1, 2])
        self.assertEqual(crossings(result, g.edges), 0)

    def test_crossings_counts_inverted_pairs(self):
        g, _ = self._make(
            ["a", "b", "x", "y"], [("a", "y"), ("b", "x")],
            {"a": 0, "b": 0, "x": 1, "y": 1},
        )
        self.assertEqual(crossings({0: ["a", "b"], 1: ["x", "y"]}, g.edges), 1)
        self.assertEqual(crossings({0: ["a", "b"], 1: ["y", "x"]}, g.edges), 0)
        # edges spanning ranks are not crossing partners until bent (#52)
        g2, _ = self._make(
            ["a", "b", "x", "y", "z"],
            [("a", "z"), ("b", "x"), ("x", "z")],
            {"a": 0, "b": 0, "x": 1, "y": 1, "z": 2},
        )
        self.assertEqual(
            crossings({0: ["a", "b"], 1: ["x", "y"], 2: ["z"]}, g2.edges), 0
        )


@unittest.skip("stage 3 (#50) not implemented")
class TestPlace(unittest.TestCase):
    pass


@unittest.skip("stage 4 (#51) not implemented")
class TestRegions(unittest.TestCase):
    pass


@unittest.skip("stage 5 (#52) not implemented")
class TestNudgeAndIntegration(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()

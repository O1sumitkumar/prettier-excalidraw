"""Tests for the auto-layout package (scripts/layout). One class per stage; stages
not yet implemented are skipped so contributors can add their class as they land."""
import os, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "prettier-excalidraw", "scripts")
sys.path.insert(0, SCRIPTS)

from layout import from_spec, direction, layout  # noqa: E402


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


@unittest.skip("stage 1 (#48) not implemented")
class TestRank(unittest.TestCase):
    pass


@unittest.skip("stage 2 (#49) not implemented")
class TestOrder(unittest.TestCase):
    pass


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

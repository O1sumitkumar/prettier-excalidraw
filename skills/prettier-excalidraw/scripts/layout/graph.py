"""Spec -> graph model shared by every layout stage. Standard library only.

The model is what the stages read and write; they never look at the spec or at
Excalidraw JSON. See README.md for the contract.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

NODE_KINDS = ("box", "diamond", "ellipse", "note", "image")


@dataclass
class Node:
    id: str
    kind: str
    w: float
    h: float
    parent: Optional[str] = None          # container id or None for top level
    fixed: Optional[Tuple[float, float]] = None
    x: Optional[float] = None             # set by place.py
    y: Optional[float] = None


@dataclass
class Edge:
    src: str
    dst: str
    label_w: float = 0.0                  # px, for inter-rank gaps
    dashed: bool = False


@dataclass
class Container:
    id: str
    title_w: float = 0.0
    parent: Optional[str] = None
    children: List[str] = field(default_factory=list)   # node and container ids
    fixed: Optional[Tuple[float, float]] = None
    w: Optional[float] = None             # set by regions.py (or from the spec)
    h: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None


@dataclass
class Graph:
    direction: str = "lr"
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    containers: Dict[str, Container] = field(default_factory=dict)
    root: List[str] = field(default_factory=list)       # top-level node and container ids

    def children(self, container_id):
        """Direct children (node and container ids) of a container, or the root list."""
        return self.root if container_id is None else self.containers[container_id].children

    def edges_within(self, container_id):
        """Edges whose endpoints (lifted to this container's level) are both children."""
        kids = set(self.children(container_id))
        out = []
        for e in self.edges:
            a, b = self.lift(e.src, container_id), self.lift(e.dst, container_id)
            if a in kids and b in kids and a != b:
                out.append(Edge(a, b, e.label_w, e.dashed))
        return out

    def lift(self, element_id, container_id):
        """The child of `container_id` that contains `element_id` (or the id itself)."""
        cur = element_id
        while cur is not None:
            parent = self._parent_of(cur)
            if parent == container_id:
                return cur
            cur = parent
        return None

    def _parent_of(self, element_id):
        if element_id in self.nodes:
            return self.nodes[element_id].parent
        if element_id in self.containers:
            return self.containers[element_id].parent
        return None


def direction(spec):
    d = spec.get("layout", "lr")
    if d not in ("lr", "tb"):
        raise ValueError(f"layout must be 'lr' or 'tb', not {d!r}")
    return d


def _contains(outer, x, y, w, h):
    return (outer["x"] <= x and outer["y"] <= y and x + w <= outer["x"] + outer["w"]
            and y + h <= outer["y"] + outer["h"])


def from_spec(spec, measure, label_px=11.0, label_pad=40.0):
    """Build the model. `measure(item) -> (w, h)` returns the size build.py will use.

    Parent resolution, in order: an explicit `"in": "<region id>"` key; otherwise
    the innermost region (by area) whose explicit bounds contain the element's
    explicit position; otherwise top level.
    """
    g = Graph(direction=direction(spec))
    regions = [it for it in spec["elements"] if it["type"] == "region"]
    for it in regions:
        if not it.get("id"):
            raise ValueError("every region needs an id for auto-layout")
        fixed = (it["x"], it["y"]) if "x" in it and "y" in it else None
        g.containers[it["id"]] = Container(id=it["id"], title_w=len(it.get("title", "")) * label_px,
                                          fixed=fixed, w=it.get("w"), h=it.get("h"),
                                          x=it.get("x"), y=it.get("y"))
    placed_regions = [r for r in regions if all(k in r for k in ("x", "y", "w", "h"))]

    def parent_for(it, w, h):
        if it.get("in"):
            if it["in"] not in g.containers:
                raise ValueError(f"{it.get('id')}: unknown region in 'in': {it['in']}")
            return it["in"]
        if "x" in it and "y" in it:
            inside = [r for r in placed_regions if r.get("id") != it.get("id") and _contains(r, it["x"], it["y"], w, h)]
            if inside:
                return min(inside, key=lambda r: r["w"] * r["h"])["id"]
        return None

    for it in spec["elements"]:
        t = it["type"]
        if t in NODE_KINDS and it.get("id"):
            w, h = measure(it)
            fixed = (it["x"], it["y"]) if "x" in it and "y" in it else None
            g.nodes[it["id"]] = Node(id=it["id"], kind=t, w=w, h=h, parent=parent_for(it, w, h), fixed=fixed)
    for it in regions:
        c = g.containers[it["id"]]
        c.parent = parent_for(it, it.get("w", 0), it.get("h", 0))
    for cid, c in g.containers.items():
        (g.root if c.parent is None else g.containers[c.parent].children).append(cid)
    for nid, n in g.nodes.items():
        (g.root if n.parent is None else g.containers[n.parent].children).append(nid)
    for it in spec["elements"]:
        if it["type"] == "arrow":
            if it["from"] not in g.nodes and it["from"] not in g.containers:
                raise ValueError(f"arrow from unknown id {it['from']}")
            if it["to"] not in g.nodes and it["to"] not in g.containers:
                raise ValueError(f"arrow to unknown id {it['to']}")
            lw = len(it.get("label", "")) * label_px + (label_pad if it.get("label") else 0)
            g.edges.append(Edge(it["from"], it["to"], lw, bool(it.get("dashed"))))
    return g

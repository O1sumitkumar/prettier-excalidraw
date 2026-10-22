# Auto-layout: design

Tracking issue: #9. Stages: #48 rank, #49 order, #50 place, #51 regions, #52 nudge
and integration. This note is the contract between them. Read it before taking a
stage; propose changes to it in the stage's PR rather than silently diverging.

## Goal

A spec may omit `x` / `y` on any element. `build.py` fills them in so that the
result builds and lints clean (no `box-overlap`, `arrow-through-box`,
`arrow-through-text`, `text-overlap`, `text-on-region-edge`), on the 20 px grid,
with the gaps from the style guide. Explicit coordinates always win: an element
that has `x` and `y` is never moved.

## Shape of the solution

Layered graph layout, the Sugiyama family, kept deliberately simple:

```
spec ──► graph.py ──► rank.py ──► order.py ──► place.py ──► regions.py ──► nudge.py ──► spec with x/y
          model         ranks      orders       coords       sizes+offsets   fixes
```

Each stage is a pure function over the shared model in `graph.py`. Stages do not
read the spec or the Excalidraw JSON; they read and write the model. `__init__.py`
exposes `layout(spec, measure) -> spec`, which runs the pipeline and writes
coordinates back only into elements that lacked them.

## The model (`graph.py`, done)

```python
Graph(direction="lr"|"tb", nodes={id: Node}, edges=[Edge], containers={id: Container}, root=[ids])
Node(id, kind, w, h, parent, fixed)        # kind: box|diamond|ellipse|note|image; fixed: (x, y) or None
Edge(src, dst, label_w, dashed)            # label_w in px for gap computation; 0 when unlabelled
Container(id, title_w, parent, children, fixed, w, h, x, y)
```

- `w` / `h` are the sizes the builder will use, obtained through the `measure`
  callback (`build.py`'s label measurement and widening rules), so layout and build
  agree on every box size.
- `parent` is the innermost region whose bounds would contain the element, or the
  region named by an explicit `"in": "<region id>"` key (new, optional, so a spec
  without coordinates can still say what goes where). Elements with neither are
  top level.
- `fixed` is the element's explicit `(x, y)` or `None`.
- Arrows between an element and a region attach to the region as a node.

`graph.py` also provides `direction(spec)`: `"layout": "lr"` (default) or `"tb"`.

## Rules that apply to every stage

1. **Explicit coordinates win.** A fixed node keeps its `x` / `y`. A container is
   laid out automatically only when *none* of its children is fixed; a container
   with a mix gets its unfixed children placed in a row 60 px below the lowest fixed
   child, with a warning (`layout: mixed container <id>`). Keep this rule in v1; a
   smarter "fit around fixed nodes" can come later.
2. **Recursion by container.** Each container is laid out as its own small graph
   (its direct children, with edges to outside nodes treated as attaching to the
   container boundary), then sized, then placed as a single node in its parent.
3. **Grid and gaps.** Every coordinate snaps to 20 px. Siblings in a rank: 20 px
   apart. Between ranks: the widest label on any edge between those ranks, computed
   as `11 px × label length + 40`, with a floor of 120 px and a ceiling of 400 px.
   Inside a region: 40 px side inset, 60 px below the top edge for the title row,
   40 px above the bottom edge.
4. **Determinism.** Same spec, same result. Ties break on element order in the spec.
5. **No new dependencies.** Standard library only.

## Stage contracts

| Stage | Function | Input → output | Tests to ship |
|---|---|---|---|
| #48 rank | `rank(graph, container_id) -> {node_id: int}` | children of one container → rank per child; sources 0; longest path; cycles broken by dropping the back edge found last; isolated nodes rank 0 | chain, diamond DAG, cycle, disconnected |
| #49 order | `order(graph, container_id, ranks) -> {rank: [node_ids]}` | barycentre sweeps down then up; keep the lower crossing count; `crossings()` helper | a case naive order crosses and barycentre fixes; stable with no edges |
| #50 place | `place(graph, container_id, orders) -> None` (writes `node.x`, `node.y`) | rank axis along `direction`; cross-axis centred; gaps per rule 3 | grid alignment, no overlaps, builds and lints clean |
| #51 regions | `size_containers(graph) -> None` | post-order: lay out children, set container `w`/`h` from their bounds plus insets, then treat as a node | two levels of nesting; title row kept clear |
| #52 nudge + integration | `nudge(graph, lint_findings) -> bool` and the `build.py` hook | shift along the rank axis, pick a different `bend`, move a label; bounded passes; `build.py` calls `layout()` when any element lacks `x`/`y` or `--layout` is given | every example spec with coordinates stripped builds and lints clean |

Stages #48, #49 can be built and tested in isolation now. #50 needs #48/#49.
#51 needs #50. #52 needs all of them. Take them in order, or coordinate on the
tracking issue.

## What is out of scope for v1

Edge routing beyond what `build.py` already does (orthogonal, one `bend`), port
assignment on specific sides, minimising total edge length, and layout of
`divider` / free `text` elements (they stay where the spec puts them).

## Where things go

```
scripts/layout/
  README.md      this note
  __init__.py    layout(spec, measure) -> spec   (wires stages; raises until #52)
  graph.py       model + from_spec()            (done)
  rank.py        #48
  order.py       #49
  place.py       #50
  regions.py     #51
  nudge.py       #52
tests/test_layout.py   one class per stage
```

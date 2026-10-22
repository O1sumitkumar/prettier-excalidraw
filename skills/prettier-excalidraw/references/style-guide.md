# Style guide

Derived from eight reference diagrams by the skill's author (839 elements measured).
Values in backticks are literal Excalidraw JSON.

## 1. Baseline for every element
```
roughness: 0            strokeStyle: "solid"      opacity: 100
strokeColor: "#1e1e1e"  fillStyle: "solid"        roundness: null (sharp corners)
canvas viewBackgroundColor: "#ffffff"
```

## 2. Text
```
fontFamily: 8  (Comic Shanns, monospace)  - alternative 6 (Nunito) for a softer look
fontSize: 16 | 20 | 28    small label | default | title / layer strip
strokeColor: "#1e1e1e"    coloured only to match a coloured arrow
in-box label: textAlign "center", verticalAlign "middle", bound via containerId
lineHeight: 1.25
```
Labels are lowercase and short: `history-service`, `task-queue`, `sdk runtime`.
Secondary info goes in square brackets: `Temporal Server` / `[durable execution engine]`,
`prod vpc [10.20.0.0/16]`. Region titles are free text inside the region at the
top-left or top-right, in brackets: `[ worker-script ]`.

## 3. Boxes
```
type: "rectangle"  roundness: null  strokeWidth: 2 (1 for small inner boxes)
```
Typical component box 240–270 × 60–70 px with icon left and label centred.
Small inner box 100–140 × 40–60 px, fontSize 16. Layer / title strips span the full
width, fontSize 28.

| Role                                   | name      | fill      |
|----------------------------------------|-----------|-----------|
| service / worker / compute / client    | blue      | `#a5d8ff` |
| server / runtime / core / CLI          | yellow    | `#ffec99` |
| gateway / network / success           | green     | `#b2f2bb` |
| storage / cache / warning              | red       | `#ffc9c9` |
| control plane / provider               | purple    | `#d0bfff` |
| external tool / observability          | orange    | `#ffd8a8` |
| kubernetes cluster                     | teal      | `#96f2d7` |
| interfaces (docs, portal, API)         | cyan      | `#99e9f2` |
| user / neutral                         | grey      | `#ced4da` |
| note / annotation                      | lightgrey | `#e9ecef` |

Stroke colour never changes with the fill. 4–7 fills per diagram. Brand colours
(Redis red, Postgres blue) appear only inside logos, never as a box fill.

## 4. Regions (containers)
```
type: "rectangle"  strokeWidth: 2  backgroundColor: tint or "transparent"
tints: blue #e7f5ff  teal #e6fcf5  yellow #fff9db  orange #fff4e6  purple #f3f0ff  red #fff5f5
```
Nesting alternates so each level reads as a layer: tinted region → white or
transparent inner box → coloured component boxes. Up to four levels is fine.
A loose group that is not a real container: `strokeStyle: "dotted"`, `opacity: 60`,
`strokeWidth: 1`.

## 5. Connectors
```
type: "arrow"  elbowed: true  strokeWidth: 2  roughness: 0
startArrowhead: null   endArrowhead: "triangle_outline"   (alternative: "triangle")
startBinding / endBinding set (fixedPoint on the side, gap 5)
strokeColor: "#1e1e1e" | "#e03131" blocked / danger / private | "#2f9e44" allowed / success | "#1971c2" info
```
Bidirectional only for client ↔ server style exchanges. Arrow labels are short free
text (size 16–20) beside the arrow in the arrow's colour. Route around boxes; when a
line must cross something, cross a transparent or white box, not a coloured one.

## 6. Icons
- Embedded images (`type: "image"`, base64 in `files`, sha1 of the bytes as id) for
  named technologies; Excalidraw-library vector icons (grouped, roughness 1) for
  generic things like laptop, users, database cylinder, browser window.
- In a labelled box: height 65–95 % of the box height, 12–20 px inset on the left,
  label centred in the box.
- Standalone: 90–250 px, name as centred text below.
- Icons in a row (e.g. GCP / AWS / Azure) are equal height and evenly spaced.
- Never stretched: `scale: [1, 1]`, aspect ratio of the source file.

## 7. Z-order (order in the `elements` array)
1. region tints / large containers
2. inner white or transparent boxes
3. component boxes, each followed by its bound label
4. icons and free text
5. arrows - always last, so no fill can hide them

## 8. Layout
Left→right for request flows, top→bottom for layered architectures. A store, cache
or queue sits directly below or beside its owner, never under something that does not
use it; proximity is read as ownership before arrows are. Layer diagrams
stack full-width layers with a coloured title strip above each. ~20 px between
siblings, 30–40 px inset inside a region, ≥ 120 px between boxes joined by a labelled
arrow. Snap to a 20 px grid.

## 9. Lint rules
| rule | meaning | fix.py |
|---|---|---|
| roughness | roughness ≠ 0 outside a library icon group | yes |
| font | fontFamily not the configured one | yes |
| font-size | not 16 / 20 / 28 or fractional | yes (snaps) |
| fill-style | hachure / cross-hatch | yes |
| stroke-style | unknown strokeStyle value | manual |
| rounded-corners | rectangle with roundness | yes |
| arrowhead | end/start head not the configured triangle | yes |
| arrow-hidden | arrow drawn before a filled box it crosses | yes (moves arrows last) |
| child-before-parent | box drawn before its container | yes |
| dark-fill-text | text on a fill too dark to read | manual |
| no-arrowhead | arrow with no head (probably a line) | manual |
| unbound-arrow | endpoint touches a box but is not bound | manual |
| icon-size | icon outside 55–100 % of its box height | manual |
| icon-stretched | image scale ≠ [1, 1] | manual |
| icon-low-contrast | SVG icon colour below 3:1 contrast on its box fill | manual |
| arrow-through-box | a connector crosses a component box it is not bound to | manual |
| arrow-overlap | two connectors share a collinear segment (> 20 px) | manual |
| text-over-box | free text lies over a component box it is not bound to | manual |
| box-overlap | two component boxes intersect without one containing the other | manual |
| text-overlap | two text elements intersect | manual |
| arrow-through-text | a connector segment crosses a free text element (title, caption) | manual |
| misleading-proximity | a store (red fill) sits directly under a non-store box it has no arrow to | manual |

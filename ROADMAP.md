# Roadmap

Where the skill is going after v0.2.0. Items are grouped by what they unlock, with a
rough size (S = an afternoon, M = a few days, L = a week or more) and the reason each
one earns its place. Order inside a group is suggested priority. Nothing here is
scheduled; pick by need.

## 1. Output formats

### 1.1 PNG / SVG export next to the `.excalidraw` file  (M) — done in `export.py`
**What.** `export.py diagram.excalidraw out.png [--scale 2] [--svg]`, and a
`"png": true` option in the spec / a `--png` flag on `build.py`, so a user who asks
for "a diagram for the README" gets both the editable file and an image.
**Why.** Most people consuming a diagram never open Excalidraw; today they need the
preview recipe and Chrome by hand.
**How.** `preview.py` already lays out everything at the exact coordinates
Excalidraw uses. Make it faithful rather than rough: embed Comic Shanns / Nunito as
`@font-face` data URIs (both are open-licence), draw hand-drawn library icons and
dashed / dotted strokes properly, then rasterise with headless Chrome when present
and fall back to quick-look on macOS. Keep stdlib only.

### 1.2 Animated, hoverable HTML export  (M) — #67, with `link` on shapes #66
**What.** `export.py diagram.excalidraw out.html`: the same SVG as 1.1 wrapped in a
single page where arrows flow in their direction, hovering a shape lights up its
connections and fades the rest, a button plays a request path one arrow at a time,
and shapes with a `link` open it. `"link"` also lands in the `.excalidraw` file,
where Excalidraw shows it on hover.
**Why.** The `.excalidraw` file is the editable source and cannot animate; a docs
page or a demo wants motion and click-through. Same layout and fonts, so the two
never disagree.
**How.** Group each element in the exported SVG with its id and arrow bindings
(`data-from` / `data-to`), then ~25 lines of CSS and ~20 of script. Proven in a
throwaway page on the payment example; #67 has the CSS.

## 2. Input formats

### 2.1 Replicate a diagram from a shared image  (M) — done
**What.** User pastes or links a PNG / JPG / screenshot of someone else's
architecture diagram; the skill rebuilds it in house style as `.excalidraw`.
**Why.** Diagrams arrive from blog posts, vendor docs and slides; people want the
same content in their own style, editable.
**How.** Claude reads the image (multimodal). A new reference
`references/reading-a-diagram.md` gives a fixed extraction checklist: components
and their labels, containers / layers, every arrow with direction and label, the
legend and what each colour means, reading direction, what is emphasised. The
result is written as the same component list the generate step already uses, then
mapped to roles and fills (never copying the source's brand colours), then a spec.
Deliver with a short "what I changed from the original and why" note. Keep the
information architecture, not the visual style.

### 2.2 Convert structured sources: Mermaid, draw.io, PlantUML  (M–L)
**What.** `convert.py in.mmd|in.drawio|in.puml spec.json` producing a spec that
`build.py` can render.
**Why.** Same need as 2.1 but with lossless input; a text converter is more reliable
than reading pixels.
**How.** Mermaid `flowchart` / `graph` parser (nodes, edges, subgraphs → regions),
draw.io mxGraph XML (cells with geometry → boxes, edges → arrows), PlantUML component
diagrams. Positions come from auto-layout (3.1) unless the source has them.

### 2.3 Diagram from code  (M–L)
**What.** "Draw what's in this repo": read `docker-compose.yml`, Kubernetes
manifests, Helm values, Terraform, and produce a component list → spec.
**Why.** The most accurate diagrams come from the source of truth, not from memory.
**How.** Small stdlib parsers per format (compose services, `depends_on`, ports,
volumes; k8s Deployments / Services / Ingress; Terraform resources by type).
Optional PyYAML if present, otherwise a minimal YAML subset reader. Output the
component list and let the gap-filling step ask about anything the files do not say.

## 3. Layout

### 3.1 Auto-layout: specs without coordinates  (L)
**What.** Allow `elements` with no `x`/`y`; `build.py` places them.
**Why.** Hand-placing coordinates is where the agent spends most of its effort and
where overlaps come from; it stops scaling past ~25 components.
**How.** Layered graph layout in stdlib: rank nodes by longest path from sources
(left→right for flows, top→bottom for layered diagrams), order within a rank by
barycentre of neighbours to reduce crossings, assign positions on the 20 px grid
with the gaps from the style guide, treat regions as compound nodes sized to their
children. Run the collision lint rules afterwards and nudge until clean.

### 3.2 Large diagrams  (M, after 3.1)
Crowding rule in `lint.py` (too many boxes per region, labels under a minimum
size), automatic splitting into a top-level diagram plus one per region, and a
"zoom" convention linking them.

### 3.3 Mixed diagrams: layers plus request flow in one picture  (S–M) — done
Layer strips as a background with a left→right flow drawn across them. `build.py`
offsets straight arrows and bends routed ones past strip titles, and keeps labels
off titles and strip borders (#10). Still by hand: a title wider than the column.

## 4. Icons

### 4.1 Excalidraw library vector icons  (M)
**What.** `"icon": "lib:laptop"` for generic things: laptop, users, database
cylinder, browser window, globe, server, queue.
**Why.** The reference diagrams use these; image logos are wrong for generic
components and the rule "no icon rather than a wrong icon" leaves gaps.
**How.** Bundle a small set as element groups in `assets/library/*.json` (taken from
MIT-licensed Excalidraw libraries, attribution in the file), scale and place them
like images, keep them grouped and exempt from the roughness rule.

### 4.2 User-supplied icon folder  (S) — done
`"icons_dir"` in the spec or a `PRETTIER_EXCALIDRAW_ICONS` environment variable;
match by label slug before falling back to Simple Icons.

### 4.3 Icon colour on light fills  (S) — done
Pick a darker Simple Icons colour automatically when the brand colour has low
contrast against the box fill (the lint already knows how to measure luminance).

## 5. Style as data

### 5.1 Style profiles: derive a style from someone's own diagrams  (M) — done in `profile.py`
**What.** `profile.py <folder of .excalidraw>` measures font, roughness, arrowheads,
fills, sizes, icon ratios and z-order habits and writes a `style.json`; `build.py`,
`lint.py`, `fix.py` take `--style style.json`.
**Why.** This is how the house style in v0.2.0 was made, by hand. Making it a
script turns the skill from "one person's style" into "your style", which is what
most people adopting an open-source skill will want.
**How.** The analysis is already written (counts per property, palette extraction,
icon-to-box ratios); package it, add a review step that shows the derived profile
before it is used, and make the current house style the default profile.

### 5.2 Per-project style config  (S, after 5.1)
`.prettier-excalidraw.json` in a repo root, picked up automatically.

## 6. Restyle robustness

- Opt-in conversion of straight arrows to elbowed routes and binding of loose
  endpoints (both move points, so off by default)  (M)
- Excalidraw frames (`frameId`) treated as regions  (S)
- `fix.py` bumps `versionNonce` as well as `version`  (S)
- `misleading-proximity` keyed on role, not only on the red fill  (S)
- Configurable exemption list for sketchy library icons instead of the
  "group with no text" heuristic  (S)

## 7. Quality and triggering

- Rerun description optimisation with the 20-query trigger set at
  `evals/trigger_eval_set.json` using 2 workers (rate limits broke the last two
  runs)  (S)
- Iteration 3 evals built from real failures collected in use, plus the hard cases:
  25+ components, from-code, messy restyle, user icon folder, mixed layers + flow  (M)
- Confirm in Excalidraw itself that elbowed bound arrows re-route when a box is
  dragged and bound labels stay centred (manual check, not yet done)  (S)

## Known limitations today

- Positions are hand-chosen by the agent; expect two or three preview rounds.
- Only image icons can be placed; library vector icons cannot.
- `preview.py` uses a stand-in font and simplifies hand-drawn icons.
- Quick-look thumbnails crop wide diagrams unless `--square` is used.
- Triggering was spot-checked, not measured at scale.

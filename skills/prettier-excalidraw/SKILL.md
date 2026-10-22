---
name: prettier-excalidraw
description: Create, restyle and lint Excalidraw (.excalidraw) architecture diagrams in a clean, opinionated house style - architect roughness, Comic Shanns font, hollow-triangle elbow arrows, light colour-coded boxes, tinted regions, properly layered z-order and proportionally sized logo icons. Use this whenever the user asks for an architecture, system, infrastructure, network, data-flow, workflow or layered diagram as an Excalidraw file, asks to "make this diagram prettier", to clean up / normalise / fix the style of an existing .excalidraw file, or mentions Excalidraw at all - even if they do not say "style". Also use it to check an .excalidraw file against the style rules.
---

# prettier-excalidraw

Produce Excalidraw diagrams that look like they were drawn by one careful person: no
sketchy lines, one font, one arrow style, a small palette of light fills with meaning,
regions that contain their children, and arrows that are never hidden behind a box.
The style is fully specified in `references/style-guide.md`; the scripts in `scripts/`
make it mechanical so you can spend your effort on layout and meaning instead of JSON.

## Which job is this?

| User wants | Do |
|---|---|
| A new diagram | **Generate**: write a spec, `build.py`, preview, lint, deliver |
| An existing `.excalidraw` made prettier / consistent | **Restyle**: `lint.py` → `fix.py` → `lint.py`, then hand-fix the manual findings |
| "Does this follow the style?" | **Check**: `lint.py` and explain the findings |

All scripts are Python 3 standard library only and live in `scripts/`. Run them from
that directory (they import each other) or set `PYTHONPATH` to it.

## Generate a new diagram

1. **Understand the system first, and fill the gaps out loud.** List the components,
   which ones are grouped (cluster, VPC, layer, process), and every connection with
   its direction and what flows over it. Prompts are usually short, so check each of
   these before drawing anything:
   - every data store, cache, queue or topic: **who reads it and who writes it?**
   - every edge: which way does it go, sync call or async event, what is the payload?
   - every boundary: what is inside it and what is outside?
   - every external system: is it called, or does it call back (webhooks)?
   If the prompt does not answer one of these and the answer changes the picture, ask
   the user one short question before building. If you cannot ask, pick the most
   likely answer (the service that owns the domain owns its store; a cache sits with
   the service that is latency-sensitive) and say so in the reply as an explicit
   assumption, so the user can correct it in one word instead of discovering it later.
   A diagram that is wrong about the system cannot be rescued by styling.
   Decide the reading direction: left→right for request flows, top→bottom for layered
   architectures.

2. **Assign fills by role**, not at random. Same kind of thing = same colour, and keep
   it to 4–7 fills per diagram. The default mapping (blue = service / compute,
   yellow = server / runtime / CLI, green = gateway / network, red = storage / cache,
   purple = control plane, orange = external tool, teal = kubernetes, cyan = interfaces,
   grey = user / neutral) is in the style guide; deviate when the user's domain needs
   different groupings, but stay consistent inside the diagram.

3. **Write the spec** (`references/spec-format.md`) as JSON. Lay elements out on a
   20 px grid with these gaps, because the builder places labels relative to them:
   - ≥ 120 px between two boxes joined by a labelled arrow (room for the label)
   - 30–40 px inset from a region border to its first child, ≥ 20 px between siblings
   - leave ~40 px above a region for its title when the title is outside
   Place a store, cache or queue directly below or beside the component that uses it,
   never under a box that does not touch it: readers infer ownership from proximity
   before they read arrows, so a cache parked under the gateway "belongs" to the
   gateway no matter what the arrow says. If two services share a store, put it
   between them. Label the arrow with the operation (`writes payments`,
   `get/set idempotency key`), not just a noun.
   Give every box and region an `id`; arrows reference those ids. Pick `from_side` /
   `to_side` so an arrow leaves a box on the side that faces its target and does not
   cross other boxes; use `from_offset` / `to_offset` to fan out several arrows from one
   side. Use `label_at` ("start" / "end") when two arrow labels would land on the same
   segment.

4. **Icons.** Add a logo for every named technology (Postgres, Kafka, Kubernetes, AWS…)
   because that is what makes an architecture diagram instantly readable. Sources, in
   order of preference:
   - the user's own icon folder. If they have one, put it in the spec as
     `"icons_dir": "path"` (or set `PRETTIER_EXCALIDRAW_ICONS`) and write
     `"icon": "auto"` on every box: the builder matches the label against the file
     names and leaves a box bare when nothing matches. Ask where their icons live if
     they mention having some.
   - Simple Icons as SVG: `curl -sL https://cdn.simpleicons.org/<slug> -o icons/<slug>.svg`
     (`<slug>` is the lowercase brand name, e.g. `postgresql`, `apachekafka`,
     `kubernetes`, `amazonaws`, `redis`, `grafana`). A missing slug downloads an
     empty or HTML file, so check the result starts with `<svg` before using it.
     Brand colours like Backstage teal or Vault yellow vanish on a light fill; add
     `/<hex>` to fetch a darker version, e.g. `kubernetes/326CE5`, `vault/000000`.
   - no icon. Never substitute a wrong or generic icon for a named product.
   Put the icon on a box with `"icon": "icons/x.svg"` (builder sizes it to ~80 % of the
   box height, on the left) or as a standalone `image` element with a `label` under it
   for big logos. Keep icon files next to the spec; paths are relative to the spec.

5. **Build, preview, lint, look.**
   ```bash
   cd <skill>/scripts
   python3 build.py spec.json out.excalidraw      # writes the file, prints size warnings
   python3 preview.py out.excalidraw out.svg            # SVG render for a visual check
   # to PNG: headless Chrome gives an exact-size image (recipe in
   # references/spec-format.md "Rendering"); fallback on macOS without Chrome:
   #   python3 preview.py out.excalidraw out.svg --square && qlmanage -t -s 2400 -o . out.svg
   python3 lint.py out.excalidraw
   ```
   Actually look at the preview. Things to catch: a box whose nearest neighbour above
   it is not the thing it talks to (`lint.py` flags this as `misleading-proximity`),
   an arrow crossing a box it is not connected to, two labels on top of each other, a label on top of a line, a box that
   the builder widened (see its warnings) now overlapping a neighbour, a region whose
   children spill outside it. Fix the spec and rebuild; two or three rounds is normal.
   The preview uses a stand-in font, so text may be a little narrower or wider than in
   Excalidraw - leave margin.

6. **Deliver** the `.excalidraw` file (and the spec, so the user can regenerate). If the
   user wants an image too, or the diagram is going into a README, slide or chat, add
   `--png` (or `--svg`) to `build.py`, or run `export.py diagram.excalidraw out.png` on
   any existing file; the export embeds the real fonts and keeps the exact layout. Say
   what each colour means in one line, since colour coding is only useful if the reader
   knows the key.

## Restyle an existing diagram

```bash
python3 lint.py in.excalidraw                 # what is wrong, with element ids
python3 fix.py in.excalidraw out.excalidraw   # mechanical fixes, positions untouched
python3 lint.py out.excalidraw                # what remains needs a human
```
`fix.py` changes font, snaps font sizes to 16/20/28 (re-measuring the text box and
re-centring bound labels), sets roughness 0, solid fills, sharp corners, the arrowhead,
moves arrows to the end of the z-order and moves a child box after its container. It
leaves grouped library icons alone (they are hand-drawn on purpose) and never moves a
shape. It prints `check label:` for any text whose size changed by 4 px or more,
because a 6 px label that becomes 16 px can now collide with its neighbours; look at
those in the preview. Findings marked `(manual)` - dark fill behind text,
unbound arrow endpoints, icon too small for its box - need judgement: edit the JSON
directly (the finding gives the element id) or tell the user what to change.

Both scripts take `--font comic|nunito` and `--arrowhead outline|filled` when the user
prefers the alternative; the default is Comic Shanns and the hollow triangle.

## Why these rules (so you can apply them to cases the rules do not cover)

- **Roughness 0 and one font** - sketchiness reads as "draft". These diagrams are
  meant to be final documentation.
- **Light fills, dark stroke** - the stroke never changes with the fill, so the eye
  groups by colour without borders competing. Text stays readable on every fill.
- **Hollow triangle, elbowed** - a minimal head keeps dense diagrams calm; right-angle
  routes make it obvious which box an arrow enters. Colour on an arrow is semantic:
  red = blocked / danger / private path, green = allowed / success, blue = informational.
- **Z-order** - regions first, then inner boxes, then component boxes, labels and
  icons, arrows last. Anything else hides something. The builder enforces this order;
  `fix.py` restores it.
- **Icons proportional to their box** (65–95 % of height) - an oversized logo turns a
  component into an advertisement, an undersized one is noise.
- **Lowercase terse labels with `[secondary info]` in brackets** - matches the
  reference diagrams and keeps boxes small.

Reference diagrams in `assets/examples/` show the finished look; open one in Excalidraw
or run `preview.py` on it when unsure what "right" looks like.

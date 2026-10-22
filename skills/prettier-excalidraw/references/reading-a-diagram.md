# Reading a diagram you did not draw

Use this when the user shares a picture of a diagram (screenshot, PNG from a blog,
vendor doc, slide) and wants it rebuilt in house style. The goal is to keep the
**information architecture** and drop the **visual style**. You are not tracing a
picture; you are re-expressing a system.

## 1. Extract, in this order

Work through the image once per item. Write the answers down as you go; they
become the component list the generate workflow starts from.

1. **Title and purpose.** What is the diagram of? One line.
2. **Containers.** Every zone, region, cluster, layer, swimlane or grouping line,
   with its label and what sits inside it. Nested containers: note the nesting.
3. **Components.** Every box, icon, cylinder, cloud or actor, with its exact label.
   Keep the subtitle text too (`REST, 50k rps`, `24h retention`); it becomes the
   bracketed second line.
4. **Connections.** Every arrow: from, to, direction, label, and style (solid,
   dashed, double-headed, colour). A dashed or differently coloured arrow usually
   means async, optional, or alarm; record the meaning, not the dash.
5. **Legend and colour meaning.** If there is a key, copy it. If there is not,
   infer what each colour groups (same colour = same kind) and write that down as
   a hypothesis.
6. **Reading direction and emphasis.** Left to right or top to bottom; what is
   biggest or central; what is pushed to the edge.
7. **What is implied but not drawn.** A store with no owner, an arrow with no
   label, a component in a zone with nothing connected. These are the gap-filling
   questions (SKILL.md, generate step 1). Ask or state assumptions, as usual.

## 2. Map onto the house style

| In the source | In the rebuild |
|---|---|
| Zone, cluster, VPC, layer, swimlane | `region` with the same title in `[ brackets ]`; nested zones stay nested |
| Service, app, function, job | `box`, fill by role (blue service, yellow runtime, green gateway or network) |
| Database, cache, bucket, queue, topic, stream | `box`, red fill, placed under or beside its owner |
| External SaaS, third party | `box`, orange fill, outside the main region |
| User, client, team, actor | `box` grey, or `ellipse` for a flowchart actor |
| Monitoring, alerting, ops tooling | `box` purple |
| Decision | `diamond`; start or end marker | `ellipse` |
| Callout, caveat, SLA, footnote | `note` |
| Brand icon in a box | fetch the real logo with `icons.py`; never recreate it from the picture |
| Source colours | dropped; roles decide fills. Keep only a colour that carries meaning the key explains, and then via the arrow colours (red blocked, green allowed, blue info) |
| Curved, diagonal or free-form arrows | elbowed arrows between the same endpoints; same label, same direction |
| Dashed arrow | `dashed: true` only if it means something (async, optional, alarm); say what in the label |
| Gradients, shadows, dark background, rounded corners, mixed fonts | dropped |
| Subtitle inside a label | second line in `[brackets]` |

Label text: keep the source's words, lowercase them, shorten to the house length.
Do not rename components; the reader will compare the two pictures.

## 3. Decide what not to carry over

Drop decorative elements (logos used as wallpaper, numbered badges with no
meaning, duplicate arrows that say the same thing). Drop information that is only
true of the source's rendering (pixel sizes, exact positions). Keep anything a
reader could ask "where did X go?" about.

When the source is wrong or inconsistent (an arrow into nothing, a store in two
zones), do not copy the mistake silently: fix it and list it in the delivery note.

## 4. Deliver

Same as a generated diagram, plus a short **changes from the original** note:

- components renamed, merged, split or dropped, and why
- arrows added (gap filling) or removed (duplicates)
- colour meaning adopted, and where it differs from the source
- anything in the source you could not read with confidence

The note is what lets the user trust the rebuild without comparing every box.

## Worked example

`docs/examples/source-clickstream.png` is a vendor-style pipeline diagram (dark
theme, gradients, curved arrows, subtitles crammed into labels). Its rebuild is
`assets/examples/clickstream.spec.json` → `clickstream.excalidraw` /
`clickstream.png`, with the extraction and the changes note in
`docs/examples/clickstream-notes.md`.

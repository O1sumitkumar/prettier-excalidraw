# Replicating a Linux network-namespace diagram

Second worked example for `references/reading-a-diagram.md`, chosen because it
exercises what the clickstream case does not: nested regions, a note box, a
region title that an arrow wants to cross, and a diagram with no logos at all.
Source: a screenshot of a tutorial-style picture (grey card titled "Linux
server", two dashed rounded boxes `netns0` / `netns1`, orange interface boxes
inside them, blue interface boxes below, a bridge `br0`, a routing-table card,
floating IP addresses, and one-directional blue/orange arrow pairs). The
screenshot is not in the repository; the rebuild is `assets/examples/netns.*`.

## Extraction

1. **Title / purpose.** How two container network namespaces reach each other
   through veth pairs and a bridge in the root namespace of one Linux host.
2. **Containers.** `Linux server` (outer card, tab-style title top right);
   `netns0` and `netns1` (dashed, rounded, side by side); `root network namespace`
   (a label only, no box, covering everything below the two namespaces).
3. **Components (label → subtitle).** netns0: `lo0`, `ceth0` → 172.18.0.10/16.
   netns1: `lo0`, `ceth1` → 172.18.0.20/16. Root: `veth0` → no IP address, `veth1`
   → no IP address, `br0` → 172.18.0.1/16, `lo0`, `eth0`. Routing table card:
   `172.18.0.0/16 via br0`.
4. **Connections.** ceth0 ↔ veth0 (drawn as a blue up arrow plus an orange down
   arrow); ceth1 ↔ veth1 (same); veth0 ↔ br0 and veth1 ↔ br0 (double-headed blue).
5. **Colour key.** None drawn. Orange = interfaces inside a container namespace,
   blue = interfaces in the root namespace, white = the bridge. Colour encodes
   namespace membership, not component role.
6. **Reading direction.** Top to bottom: containers above, host plumbing below.
7. **Implied, not drawn.** `eth0` has no link to `br0`, and both `lo0`s are
   isolated, so the picture shows no path off the host. Probably deliberate
   (the tutorial is about namespace-to-namespace traffic), so kept as drawn.

## Mapping decisions

- Namespace membership moved from box colour to region tint: yellow regions for
  `netns0` and `netns1`, a blue region for the root namespace (which the source
  only labelled). All interfaces are green, the network role in the house style,
  and a key line under the diagram says so.
- The outer card became a transparent region titled `[ linux server ]`, title
  top right as in the source. The root-namespace title is centred so the two
  veth arrows coming down from the containers do not cross it (the first build
  put it top left and the linter flagged `arrow-through-text`; one field change).
- Floating IP addresses became the bracketed second line of their interface;
  "no IP address" likewise on `veth0` and `veth1`.
- Each blue-up / orange-down pair became one `bidirectional` arrow; the bridge
  links stay double-headed as in the source. Arrow colour is the default black
  because the source's colours marked direction, not meaning.
- The routing table became a `note`; `size: 16` on every box because the labels
  are short and the diagram is dense.
- No logos: kernel interfaces have none, and a Linux penguin on the outer region
  would decorate rather than inform.

## Changes from the original

- Colour now means role (green = interface) and tint means namespace; the
  source's orange/blue split is expressed by the regions instead.
- Two one-way arrows per veth pair merged into one double-headed arrow each.
- Nothing dropped or renamed. The missing `eth0` ↔ `br0` link and the isolated
  loopbacks are kept as drawn and called out, since a reader may expect a path
  to the outside world.

#!/usr/bin/env python3
"""Check .excalidraw files against the prettier-excalidraw style guide.

Usage:
    python3 lint.py diagram.excalidraw [--font comic|nunito] [--arrowhead outline|filled]
                                       [--json] [--allow-manual] [--style style.json]
    python3 lint.py docs/diagrams/ other.excalidraw ... [--quiet]

A directory is searched recursively for *.excalidraw (hidden folders, node_modules and
__pycache__ are skipped). With more than one file the output is one line per file, the
findings of the files that have any, and a totals line; --quiet keeps only the per-file
lines and the totals. Exit code 0 = every file clean, 1 = violations found. With
--allow-manual, findings that need a human (marked "(manual)") are still printed but do
not affect the exit code, which is what a CI gate on hand-drawn reference diagrams wants.
Each finding names the element id so it can be located in the JSON. Library icons
(groups of >= 3 hand-drawn parts without text) are exempt from the roughness rule,
because the Excalidraw library ships them sketchy on purpose and they still read fine.
--json prints the findings list for one file, or {"files": [...], "summary": {...}} for
several. Standard library only.
"""
import json, os, sys
from collections import Counter
from exstyle import (ARROWHEADS, FONT_IDS, FONT_NAMES, FONT_SIZES, ICON_MIN_CONTRAST, STYLE, area, bbox, contrast,
                     inside, is_light, overlap, style_from_argv)


def load(path):
    d = json.load(open(path, encoding="utf-8"))
    return d, [e for e in d["elements"] if not e.get("isDeleted")]


def icon_groups(els):
    """group ids that look like library icons: >=3 members, none of them text."""
    members = {}
    for e in els:
        for g in e.get("groupIds", []):
            members.setdefault(g, []).append(e)
    return {g for g, ms in members.items() if len(ms) >= 3 and not any(m["type"] == "text" for m in ms)}


# Tiny register/grid cells drawn on a strip (area at or under this) are not collisions.
CELL_GRID_AREA = 2500


def cell_grid_parents(filled_rects):
    """Map cell id -> strip element for intentional small-cell grids.

    Same-sized boxes (area <= CELL_GRID_AREA, equal width and height) that sit on one
    larger box in a row or column with regular spacing: the strip is their container
    for overlap and z-order. Cells may overhang the strip (drawn on top of it).
    """
    cells = [r for r in filled_rects if area(bbox(r)) <= CELL_GRID_AREA]
    by_size = {}
    for c in cells:
        b = bbox(c)
        key = (round(b[2] - b[0]), round(b[3] - b[1]))
        by_size.setdefault(key, []).append(c)
    out = {}
    for group in by_size.values():
        if len(group) < 2:
            continue
        # try row (shared y-centre) then column (shared x-centre)
        for axis in ("row", "col"):
            def centre(r, ax=axis):
                b = bbox(r)
                return ((b[1] + b[3]) / 2, (b[0] + b[2]) / 2) if ax == "row" else ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)

            # primary = shared coordinate, secondary = along-axis sort key
            primaries = [centre(r)[0] for r in group]
            if max(primaries) - min(primaries) > 8:
                continue
            ordered = sorted(group, key=lambda r: centre(r)[1])
            secs = [centre(r)[1] for r in ordered]
            gaps = [secs[i + 1] - secs[i] for i in range(len(secs) - 1)]
            if not gaps or min(gaps) <= 0:
                continue
            if max(gaps) - min(gaps) > 12:
                continue
            # find a strip that every cell sits on (centre inside, or any overlap)
            for strip in filled_rects:
                if strip in group:
                    continue
                sb = bbox(strip)
                if area(sb) <= area(bbox(group[0])) * 1.5:
                    continue
                ok = True
                for c in ordered:
                    cb = bbox(c)
                    cx, cy = (cb[0] + cb[2]) / 2, (cb[1] + cb[3]) / 2
                    centre_in = sb[0] - 4 <= cx <= sb[2] + 4 and sb[1] - 4 <= cy <= sb[3] + 4
                    if not (centre_in or overlap(cb, sb)):
                        ok = False
                        break
                if not ok:
                    continue
                # strip should span the run of cells along the axis
                if axis == "row":
                    if sb[0] > secs[0] + 4 or sb[2] < secs[-1] - 4:
                        continue
                else:
                    if sb[1] > secs[0] + 4 or sb[3] < secs[-1] - 4:
                        continue
                for c in ordered:
                    out[c["id"]] = strip
                break
            if any(c["id"] in out for c in ordered):
                break
    return out


def lint(path, font=None, arrowhead=None):
    d, els = load(path)
    want_font = STYLE["font"] if font is None else (font if isinstance(font, int) else FONT_IDS[font])
    want_head = STYLE["arrowhead"] if arrowhead is None else ARROWHEADS.get(arrowhead, arrowhead)
    want_rough = STYLE["roughness"]
    icons = icon_groups(els)
    idx = {e["id"]: i for i, e in enumerate(els)}
    byid = {e["id"]: e for e in els}
    out = []

    def add(rule, e, msg, fixable=True):
        out.append({"rule": rule, "id": e["id"], "type": e["type"], "message": msg, "fixable": fixable})

    # Component boxes only: diamonds / ellipses are flowchart markers, so proximity and
    # box-overlap (built from filled_rects) deliberately ignore them.
    filled_rects = [e for e in els if e["type"] == "rectangle"
                    and e.get("backgroundColor") not in (None, "transparent")]
    # elements that some bound arrow starts from: a headless arrow ending on one of these
    # is the first half of a split branch (diamond -> "yes" circle -> target), not a mistake
    arrow_sources = {e["startBinding"]["elementId"] for e in els
                     if e["type"] == "arrow" and e.get("startBinding")}

    for e in els:
        t = e["type"]
        in_icon = any(g in icons for g in e.get("groupIds", []))
        if t in ("rectangle", "ellipse", "diamond", "arrow", "line", "text") and not in_icon:
            if e.get("roughness", 0) != want_rough:
                add("roughness", e, f"roughness={e['roughness']} (want {want_rough})")
        if t in ("rectangle", "ellipse", "diamond"):
            if e.get("fillStyle") not in (None, STYLE["fill_style"]):
                add("fill-style", e, f"fillStyle={e['fillStyle']} (want {STYLE['fill_style']})")
            if t == "rectangle" and STYLE["roundness"] is None and e.get("roundness") is not None and not in_icon:
                add("rounded-corners", e, "rectangle has rounded corners (want sharp)")
            has_text = any(b.get("type") == "text" for b in e.get("boundElements") or [])
            if has_text and not is_light(e.get("backgroundColor")):
                add("dark-fill-text", e, f"dark fill {e['backgroundColor']} behind text", fixable=False)
            if e.get("strokeStyle") not in (None, "solid", "dotted", "dashed"):
                add("stroke-style", e, f"strokeStyle={e['strokeStyle']}")
        if t == "text":
            if e.get("fontFamily") != want_font:
                add("font", e, f"fontFamily={FONT_NAMES.get(e.get('fontFamily'), e.get('fontFamily'))} "
                               f"(want {FONT_NAMES[want_font]})")
            fs = e.get("fontSize", 20)
            if round(fs) not in FONT_SIZES or abs(fs - round(fs)) > 0.01:
                add("font-size", e, f"fontSize={fs:.2f} (want one of {FONT_SIZES})")
        if t == "arrow":
            head = e.get("endArrowhead")
            if head is None and e.get("startArrowhead") is None and not in_icon:
                ends_on = (e.get("endBinding") or {}).get("elementId")
                if ends_on not in arrow_sources:
                    add("no-arrowhead", e, "arrow has no arrowhead (is it a connector?)", fixable=False)
            elif head is not None and head != want_head:
                add("arrowhead", e, f"endArrowhead={head} (want {want_head})")
            if e.get("startArrowhead") not in (None, want_head):
                add("arrowhead", e, f"startArrowhead={e['startArrowhead']} (want {want_head} or none)")
            if head is not None:
                ab = bbox(e)
                for r in filled_rects:
                    if idx[r["id"]] > idx[e["id"]] and overlap(ab, bbox(r)) and area(bbox(r)) > 2000:
                        add("arrow-hidden", e, f"arrow drawn before filled box {r['id']} it crosses")
                        break
                for key in ("startBinding", "endBinding"):
                    if not e.get(key):
                        # endpoint inside some box but not bound -> will not follow the box
                        px = e["x"] + (e["points"][0][0] if key == "startBinding" else e["points"][-1][0])
                        py = e["y"] + (e["points"][0][1] if key == "startBinding" else e["points"][-1][1])
                        for r in filled_rects:
                            b = bbox(r)
                            if b[0] - 8 <= px <= b[2] + 8 and b[1] - 8 <= py <= b[3] + 8 and area(b) < 60000:
                                add("unbound-arrow", e, f"{key[:-7]} touches box {r['id']} but is not bound", fixable=False)
                                break
        if t == "image":
            # proportional to a containing labelled box?
            ib = bbox(e)
            conts = [r for r in els if r["type"] == "rectangle" and inside(ib, bbox(r))
                     and area(bbox(r)) > area(ib) * 1.2 and area(bbox(r)) < 60000]
            if conts:
                r = min(conts, key=lambda r: area(bbox(r)))
                ratio = e["height"] / r["height"]
                if not 0.55 <= ratio <= 1.0:
                    add("icon-size", e, f"icon is {ratio:.0%} of box {r['id']} height (want 65-95%)", fixable=False)
            if e.get("scale") not in (None, [1, 1]):
                add("icon-stretched", e, f"image scale={e['scale']}", fixable=False)
            f = d.get("files", {}).get(e.get("fileId"), {})
            if conts and f.get("mimeType") == "image/svg+xml":
                import base64, re
                try:
                    svg = base64.b64decode(f["dataURL"].split(",", 1)[1]).decode("utf-8", "ignore")
                    m = re.search(r'<svg\b[^>]*?\sfill=["\'](#[0-9a-fA-F]{3,6})["\']', svg)
                    bg = r.get("backgroundColor")
                    if m and bg and bg != "transparent" and contrast(m.group(1), bg) < ICON_MIN_CONTRAST:
                        add("icon-low-contrast", e, f"icon colour {m.group(1)} on box fill {bg} has contrast "
                            f"{contrast(m.group(1), bg):.1f} (want >= {ICON_MIN_CONTRAST:.0f}); rebuild or set icon_color",
                            fixable=False)
                except Exception:
                    pass

    # misleading proximity: a data store / cache / queue (red fill in this style) sitting
    # directly under a non-store box it is not connected to. Readers assume the box
    # above owns the store before they read any arrow. Peers stacked in a column
    # (two services, two stores) are fine, so the rule is deliberately narrow.
    # Annotation notes (lightgrey, stroke 1, left-aligned bound text) are ignored:
    # they caption the diagram and are not ownership cues.
    STORE_FILLS = set(STYLE["store_fills"])
    NOTE_FILL = STYLE["fills"].get("lightgrey", "#e9ecef")

    def is_note(e):
        if e["type"] != "rectangle" or e.get("strokeWidth") != 1:
            return False
        if e.get("backgroundColor") != NOTE_FILL:
            return False
        return any(t.get("containerId") == e["id"] and t.get("textAlign") == "left"
                   for t in els if t["type"] == "text")

    byid_box = {e["id"]: e for e in els if e["type"] == "rectangle"
                and any(b.get("type") == "text" for b in e.get("boundElements") or [])
                and not is_note(e)}
    links = {}
    for e in els:
        if e["type"] == "arrow" and e.get("startBinding") and e.get("endBinding"):
            a, b = e["startBinding"]["elementId"], e["endBinding"]["elementId"]
            links.setdefault(a, set()).add(b); links.setdefault(b, set()).add(a)
    for b in byid_box.values():
        if b.get("backgroundColor") not in STORE_FILLS or not links.get(b["id"]): continue
        bb = bbox(b)
        above = [a for a in byid_box.values() if a is not b and area(bbox(a)) < 60000
                 and a.get("backgroundColor") not in STORE_FILLS
                 and abs(a["y"] + a["height"] - b["y"]) < 200 and a["y"] + a["height"] <= b["y"] + 1
                 and min(bbox(a)[2], bb[2]) - max(bbox(a)[0], bb[0]) > 0.5 * b["width"]]
        if above:
            a = min(above, key=lambda a: b["y"] - (a["y"] + a["height"]))
            if a["id"] not in links[b["id"]]:
                label = lambda r: next((t["text"] for t in els if t.get("containerId") == r["id"]), r["id"]).split("\n")[0]
                add("misleading-proximity", b, f"'{label(b)}' sits right under '{label(a)}' but is not connected to it; "
                    f"move the store under the box that uses it", fixable=False)

    # arrow crossing text: a connector segment running through a free text element
    # (region titles, captions) makes both unreadable
    free_text = [t for t in els if t["type"] == "text" and not t.get("containerId")]
    for e in els:
        if e["type"] != "arrow" or not e.get("endArrowhead"): continue
        pts = [(e["x"] + p[0], e["y"] + p[1]) for p in e.get("points", [])]
        for a, b in zip(pts, pts[1:]):
            seg = (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
            for t in free_text:
                tb = bbox(t)
                inner = (tb[0] + 1, tb[1] + 1, tb[2] - 1, tb[3] - 1)
                if overlap(seg, inner) and not (seg[2] - seg[0] < 1 and seg[3] - seg[1] < 1):
                    add("arrow-through-text", e, f"arrow runs through text '{t['text'][:30]}' ({t['id']}); "
                        f"offset the arrow or move the text", fixable=False)
                    break
            else:
                continue
            break

    # arrow through an unrelated box: a connector segment crossing a small filled box it is
    # not bound to. Crossing a big region is normal; crossing a component box is not.
    small_boxes = [r for r in filled_rects if area(bbox(r)) < 60000]
    connectors = [e for e in els if e["type"] == "arrow" and e.get("endArrowhead")]
    seg_list = []   # (arrow, (x0,y0,x1,y1)) for every segment, reused below
    for e in connectors:
        pts = [(e["x"] + p[0], e["y"] + p[1]) for p in e.get("points", [])]
        bound = {b.get("elementId") for b in (e.get("startBinding"), e.get("endBinding")) if b}
        for a, b in zip(pts, pts[1:]):
            seg = (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1]))
            seg_list.append((e, seg))
            ends = [(pts[0][0], pts[0][1]), (pts[-1][0], pts[-1][1])]
            hit = next((r for r in small_boxes if r["id"] not in bound
                        and overlap(seg, (bbox(r)[0] + 3, bbox(r)[1] + 3, bbox(r)[2] - 3, bbox(r)[3] - 3))
                        # an arrow may cross a box that contains its own endpoint (target nested inside it)
                        and not any(bbox(r)[0] - 8 <= px <= bbox(r)[2] + 8 and bbox(r)[1] - 8 <= py <= bbox(r)[3] + 8
                                    for px, py in ends)), None)
            if hit:
                add("arrow-through-box", e, f"arrow runs through box {hit['id']} it is not connected to; "
                    f"route around it (from_side / to_side / bend)", fixable=False)
                break

    # two connectors sharing a line: collinear segments that overlap for more than 20 px
    seen = set()
    for i, (e1, s1) in enumerate(seg_list):
        for e2, s2 in seg_list[i + 1:]:
            if e1 is e2 or (e1["id"], e2["id"]) in seen: continue
            h1, h2 = s1[3] - s1[1] < 1, s2[3] - s2[1] < 1
            v1, v2 = s1[2] - s1[0] < 1, s2[2] - s2[0] < 1
            if h1 and h2 and abs(s1[1] - s2[1]) < 3 and min(s1[2], s2[2]) - max(s1[0], s2[0]) > 20 \
               or v1 and v2 and abs(s1[0] - s2[0]) < 3 and min(s1[3], s2[3]) - max(s1[1], s2[1]) > 20:
                seen.add((e1["id"], e2["id"]))
                add("arrow-overlap", e1, f"shares a line with arrow {e2['id']}; give one of them a different "
                    f"bend or offset", fixable=False)

    # overlapping text: two text elements whose boxes intersect
    texts = [t for t in els if t["type"] == "text"]
    for i, t1 in enumerate(texts):
        b1 = bbox(t1)
        for t2 in texts[i + 1:]:
            b2 = bbox(t2)
            if overlap((b1[0] + 2, b1[1] + 2, b1[2] - 2, b1[3] - 2), (b2[0] + 2, b2[1] + 2, b2[2] - 2, b2[3] - 2)):
                add("text-overlap", t1, f"'{t1['text'][:25]}' overlaps '{t2['text'][:25]}' ({t2['id']})", fixable=False)

    # free text lying over a component box it does not belong to (a label that drifted), or
    # drawn BEFORE a filled box it overlaps (hidden under the fill; fix.py moves it up)
    for t in free_text:
        tb = bbox(t); inner = (tb[0] + 2, tb[1] + 2, tb[2] - 2, tb[3] - 2)
        behind = next((r for r in filled_rects if idx[r["id"]] > idx[t["id"]] and overlap(inner, bbox(r))), None)
        if behind:
            add("text-behind-box", t, f"'{t['text'][:25]}' is drawn before filled box {behind['id']} and hidden under it")
            continue
        hit = next((r for r in small_boxes if overlap(inner, bbox(r))), None)
        if hit:
            add("text-over-box", t, f"'{t['text'][:25]}' lies over box {hit['id']}; move the text or the arrow it labels", fixable=False)

    # intentional cell grids on a strip: tiny equal cells in a row/column, not collisions
    grid_parent = cell_grid_parents(filled_rects)
    grid_pairs = {(cid, grid_parent[cid]["id"]) for cid in grid_parent}
    grid_pairs |= {(b, a) for a, b in grid_pairs}

    # two component boxes overlapping (nesting, i.e. one fully inside the other, is fine)
    for i, a in enumerate(small_boxes):
        ab = bbox(a)
        for b in small_boxes[i + 1:]:
            bb = bbox(b)
            if (a["id"], b["id"]) in grid_pairs:
                continue
            if overlap((ab[0] + 1, ab[1] + 1, ab[2] - 1, ab[3] - 1), bb) and not inside(ab, bb) and not inside(bb, ab):
                add("box-overlap", a, f"overlaps box {b['id']}; move one of them", fixable=False)

    # a free text sitting on a region's border line is half inside, half outside: unreadable
    regions = [r for r in els if r["type"] == "rectangle" and area(bbox(r)) >= 60000]
    for t in free_text:
        tb = bbox(t)
        for r in regions:
            rb = bbox(r)
            crosses_h = (tb[1] < rb[1] < tb[3] or tb[1] < rb[3] < tb[3]) and tb[0] < rb[2] and tb[2] > rb[0]
            crosses_v = (tb[0] < rb[0] < tb[2] or tb[0] < rb[2] < tb[2]) and tb[1] < rb[3] and tb[3] > rb[1]
            if crosses_h or crosses_v:
                add("text-on-region-edge", t, f"'{t['text'][:25]}' sits on the border of region {r['id']}; "
                    f"move it inside or outside (label_at, or shift the arrow)", fixable=False)
                break

    # z-order: child rectangle before parent (strip counts as parent of its cell grid)
    for c in filled_rects:
        cb = bbox(c)
        parents = []
        if c["id"] in grid_parent:
            parents.append(grid_parent[c["id"]])
        for p in filled_rects:
            if p is c: continue
            pb = bbox(p)
            if inside(cb, pb) and area(pb) > area(cb) * 1.1:
                parents.append(p)
        for p in parents:
            if idx[p["id"]] > idx[c["id"]]:
                add("child-before-parent", c, f"drawn before its container {p['id']}")
                break
    return out


SKIP_DIRS = {"node_modules", "__pycache__"}


def collect(paths):
    """Expand files and directories to a sorted list of .excalidraw files (directories recursively)."""
    out = []
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS)
                out += sorted(os.path.join(root, f) for f in files if f.lower().endswith(".excalidraw"))
        else:
            out.append(p)
    seen = set()
    return [p for p in out if not (p in seen or seen.add(p))]


def lint_many(paths, font=None, head=None):
    """[(path, findings | None, error | None)] for every file under `paths`."""
    out = []
    for p in collect(paths):
        try:
            out.append((p, lint(p, font, head), None))
        except Exception as ex:  # unreadable, not JSON, not an Excalidraw file
            out.append((p, None, f"{ex.__class__.__name__}: {ex}"))
    return out


def _print_findings(findings):
    for f in findings:
        print(f"  [{f['rule']}] {f['type']} {f['id']}: {f['message']}" + ("" if f["fixable"] else "  (manual)"))


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0 if args else 2)
    style_from_argv(args)
    valued = {"--font", "--arrowhead", "--style"}
    opts, paths, i = {}, [], 0
    while i < len(args):
        a = args[i]
        if a in valued:
            opts[a] = args[i + 1]; i += 2
        elif a.startswith("--"):
            opts[a] = True; i += 1
        else:
            paths.append(a); i += 1
    if not paths:
        print(__doc__); sys.exit(2)
    font, head = opts.get("--font"), opts.get("--arrowhead")
    as_json, allow_manual, quiet = "--json" in opts, "--allow-manual" in opts, "--quiet" in opts

    results = lint_many(paths, font, head)
    if not results:
        print("no .excalidraw files found under " + ", ".join(paths)); sys.exit(2)
    single = len(results) == 1 and results[0][0] == paths[0] and not os.path.isdir(paths[0])

    def blocking(findings):
        return [f for f in findings if f["fixable"]] if allow_manual else findings

    if single:
        path, findings, error = results[0]
        if error:
            print(f"{path}: error {error}"); sys.exit(1)
        if as_json:
            print(json.dumps(findings, indent=1))
        elif not findings:
            print(f"{path}: clean")
        else:
            counts = Counter(f["rule"] for f in findings)
            print(f"{path}: {len(findings)} findings  " + ", ".join(f"{k}×{v}" for k, v in counts.most_common()))
            _print_findings(findings)
        sys.exit(1 if blocking(findings) else 0)

    failed = 0
    rows = []
    for path, findings, error in results:
        if error:
            failed += 1; rows.append({"path": path, "error": error, "findings": []})
        else:
            if blocking(findings):
                failed += 1
            rows.append({"path": path, "findings": findings})
    clean = sum(1 for r in rows if not r.get("error") and not r["findings"])
    summary = {"files": len(rows), "clean": clean, "with_findings": len(rows) - clean, "failed": failed}
    if as_json:
        print(json.dumps({"files": rows, "summary": summary}, indent=1))
        sys.exit(1 if failed else 0)
    for r in rows:
        if r.get("error"):
            print(f"{r['path']}: error {r['error']}")
        elif not r["findings"]:
            print(f"{r['path']}: clean")
        else:
            manual = sum(1 for f in r["findings"] if not f["fixable"])
            print(f"{r['path']}: {len(r['findings'])} findings" + (f" ({manual} manual)" if manual else ""))
    if not quiet:
        for r in rows:
            if r["findings"]:
                print(f"\n{r['path']}")
                _print_findings(r["findings"])
    print(f"\n{summary['files']} files, {clean} clean, {summary['with_findings']} with findings"
          + (f", {failed} failing" if failed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

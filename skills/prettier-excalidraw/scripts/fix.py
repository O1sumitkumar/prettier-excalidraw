#!/usr/bin/env python3
"""Rewrite a .excalidraw file so it conforms to the prettier-excalidraw style.

Usage:
    python3 fix.py in.excalidraw out.excalidraw [--font comic|nunito] [--arrowhead outline|filled]
                                                [--style style.json]

Fixes: font family, snapped font sizes, roughness, fill style, rounded
rectangles, arrowhead type, arrows moved to the end of the z-order, child
rectangles moved after their container. It never changes positions, colors
or text, so the diagram keeps its meaning; run lint.py afterwards to see what
still needs a human (dark fills, icon sizes, unbound arrows).
Standard library only.
"""
import json, sys
from exstyle import ARROWHEADS, CHAR_W, FONT_IDS, FONT_SIZES, LINE_H, STYLE, area, bbox, inside, style_from_argv
from lint import icon_groups


def snap(fs):
    return min(FONT_SIZES, key=lambda s: abs(s - fs))


def remeasure(t, byid):
    """Recompute a text element's box from its font, and re-centre it in its container.
    Excalidraw keeps stale width/height otherwise, which misplaces bound labels."""
    lines = t["text"].split("\n")
    cw = CHAR_W.get(t["fontFamily"], 0.55)
    w = max(len(l) for l in lines) * cw * t["fontSize"]
    h = len(lines) * t["fontSize"] * LINE_H
    c = byid.get(t.get("containerId"))
    if c is not None:
        t["x"] = c["x"] + (c["width"] - w) / 2
        t["y"] = c["y"] + (c["height"] - h) / 2
    elif t.get("textAlign") == "center" and abs(w - t["width"]) < 0.5 * t["width"]:
        # keep a centred caption centred, unless the size change is so large that the old
        # centre is meaningless (a 6 px label growing to 16 px); then keep its left edge so
        # it stays with the thing it was next to
        t["x"] += (t["width"] - w) / 2
    t["width"], t["height"] = w, h


def fix(doc, font=None, arrowhead=None):
    want_font = STYLE["font"] if font is None else (font if isinstance(font, int) else FONT_IDS[font])
    want_head = STYLE["arrowhead"] if arrowhead is None else ARROWHEADS.get(arrowhead, arrowhead)
    els = [e for e in doc["elements"] if not e.get("isDeleted")]
    icons = icon_groups(els)
    byid = {e["id"]: e for e in els}
    big_changes = []
    changed = 0
    for e in els:
        in_icon = any(g in icons for g in e.get("groupIds", []))
        t = e["type"]
        if t in ("rectangle", "ellipse", "diamond", "arrow", "line", "text") and not in_icon \
           and e.get("roughness", 0) != STYLE["roughness"]:
            e["roughness"] = STYLE["roughness"]; changed += 1
        if t in ("rectangle", "ellipse", "diamond") and e.get("fillStyle") != STYLE["fill_style"]:
            e["fillStyle"] = STYLE["fill_style"]; changed += 1
        if t == "rectangle" and STYLE["roundness"] is None and e.get("roundness") is not None and not in_icon:
            e["roundness"] = None; changed += 1
        if t == "text":
            before = (e.get("fontFamily"), e.get("fontSize", 20))
            if e.get("fontFamily") != want_font:
                e["fontFamily"] = want_font; changed += 1
            fs = e.get("fontSize", 20)
            if abs(fs - snap(fs)) > 0.01:
                e["fontSize"] = snap(fs); changed += 1
            e["lineHeight"] = LINE_H
            if before != (e["fontFamily"], e["fontSize"]):
                remeasure(e, byid)
                if abs(before[1] - e["fontSize"]) >= 4:
                    big_changes.append(f"{e['id']} '{e['text'][:30]}' {before[1]:.0f}->{e['fontSize']}px")
        if t == "arrow":
            if e.get("endArrowhead") not in (None, want_head):
                e["endArrowhead"] = want_head; changed += 1
            if e.get("startArrowhead") not in (None, want_head):
                e["startArrowhead"] = want_head; changed += 1
    # z-order: containers before children, arrows last
    rects = [e for e in els if e["type"] == "rectangle" and e.get("backgroundColor") not in (None, "transparent")]
    order = {e["id"]: i for i, e in enumerate(els)}
    moved = True
    while moved:
        moved = False
        for c in rects:
            for p in rects:
                if p is c: continue
                if inside(bbox(c), bbox(p)) and area(bbox(p)) > area(bbox(c)) * 1.1 and order[p["id"]] > order[c["id"]]:
                    # move c (and its bound text) right after p
                    bound_ids = {b["id"] for b in c.get("boundElements") or [] if b.get("type") == "text"}
                    block = [c] + [e for e in els if e["id"] in bound_ids]
                    for b in block: els.remove(b)
                    pi = els.index(p)
                    for k, b in enumerate(block): els.insert(pi + 1 + k, b)
                    order = {e["id"]: i for i, e in enumerate(els)}
                    changed += 1; moved = True
                    break
            if moved: break
    arrows = [e for e in els if e["type"] == "arrow" and (e.get("endArrowhead") or e.get("startArrowhead"))]
    if arrows:
        arrow_text = {b["id"] for a in arrows for b in a.get("boundElements") or [] if b.get("type") == "text"}
        tail = arrows + [e for e in els if e["id"] in arrow_text]
        head = [e for e in els if e not in tail]
        if head + tail != els:
            changed += 1
        els = head + tail
    import random
    for i, e in enumerate(els):
        e["index"] = "a" + format(i, "04d")
        e["version"] = e.get("version", 1) + 1
        e["versionNonce"] = random.randint(1, 2 ** 31 - 1)   # collab clients key change detection on it
    doc["elements"] = els
    fix.big_changes = big_changes
    return changed


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__); sys.exit(2)
    style_from_argv(args)
    font = args[args.index("--font") + 1] if "--font" in args else None
    head = args[args.index("--arrowhead") + 1] if "--arrowhead" in args else None
    doc = json.load(open(args[0], encoding="utf-8"))
    n = fix(doc, font, head)
    json.dump(doc, open(args[1], "w", encoding="utf-8"), indent=1)
    print(f"wrote {args[1]}: {n} changes")
    for b in fix.big_changes:
        print(f"  check label: {b} - a big size change can collide with neighbours")


if __name__ == "__main__":
    main()

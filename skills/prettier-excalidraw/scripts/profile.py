#!/usr/bin/env python3
"""Derive a style profile from a folder of .excalidraw files.

Usage:
    python3 profile.py <folder-or-files...> [-o style.json] [--name mine]

Measures what the diagrams actually do - font, sizes, roughness, stroke, corners,
fill style, arrowheads, elbow routing, the fills used on component boxes and on big
regions, the colours used on arrows - and writes a style.json that build.py,
lint.py and fix.py accept via --style. Prints the profile for review; derive from
diagrams you are happy with, not from everything you ever drew.
Standard library only.
"""
import glob, json, os, sys
from collections import Counter
from exstyle import FILLS, FONT_NAMES, TINTS, area, bbox, is_light
from lint import icon_groups

NAMED = {v: k for k, v in FILLS.items()}
NAMED_TINTS = {v: k for k, v in TINTS.items()}


def mode(counter, default=None):
    return counter.most_common(1)[0][0] if counter else default


def profile(paths):
    c = {k: Counter() for k in ("font", "size", "rough", "stroke", "sw", "round", "fillstyle", "head", "start",
                                "elbow", "fill", "tint", "acolor", "canvas")}
    n_files = 0
    for p in paths:
        try:
            d = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        n_files += 1
        els = [e for e in d.get("elements", []) if not e.get("isDeleted")]
        icons = icon_groups(els)
        c["canvas"][d.get("appState", {}).get("viewBackgroundColor", "#ffffff")] += 1
        for e in els:
            t = e["type"]
            in_icon = any(g in icons for g in e.get("groupIds", []))
            if in_icon:
                continue
            if t == "text":
                c["font"][e.get("fontFamily")] += 1
                c["size"][round(e.get("fontSize", 20))] += 1
            if t in ("rectangle", "ellipse", "diamond", "arrow", "text"):
                c["rough"][e.get("roughness", 0)] += 1
                c["stroke"][e.get("strokeColor")] += 1
            if t in ("rectangle", "ellipse", "diamond"):
                c["sw"][e.get("strokeWidth")] += 1
                c["fillstyle"][e.get("fillStyle")] += 1
                if t == "rectangle":
                    c["round"]["sharp" if e.get("roundness") is None else "rounded"] += 1
                bg = e.get("backgroundColor")
                if bg and bg != "transparent" and is_light(bg):
                    (c["tint"] if area(bbox(e)) >= 60000 else c["fill"])[bg.lower()] += 1
            if t == "arrow" and (e.get("endArrowhead") or e.get("startArrowhead")):
                c["head"][e.get("endArrowhead")] += 1
                c["start"][e.get("startArrowhead")] += 1
                c["elbow"][bool(e.get("elbowed"))] += 1
                c["acolor"][e.get("strokeColor")] += 1
    if not n_files:
        raise SystemExit("no readable .excalidraw files")
    stroke = mode(c["stroke"], "#1e1e1e")
    sizes = sorted(s for s, _ in c["size"].most_common(3)) or [16, 20, 28]
    fills = {}
    for hexv, _ in c["fill"].most_common(10):
        fills[NAMED.get(hexv, f"fill{len(fills) + 1}")] = hexv
    tints = {}
    for hexv, _ in c["tint"].most_common(6):
        tints[NAMED_TINTS.get(hexv, f"tint{len(tints) + 1}")] = hexv
    acolors = {"black": stroke}
    for hexv, _ in c["acolor"].most_common(6):
        if hexv and hexv.lower() not in (stroke.lower(), "#000000"):
            acolors[{"#e03131": "red", "#2f9e44": "green", "#1971c2": "blue"}.get(hexv.lower(), f"color{len(acolors)}")] = hexv
    stores = [h for n, h in fills.items() if n == "red"] or ([list(fills.values())[-1]] if fills else [])
    return {
        "name": "derived",
        "measured_from": {"files": n_files, "text": sum(c["font"].values()), "shapes": sum(c["sw"].values()),
                          "arrows": sum(c["head"].values())},
        "font": mode(c["font"], 8), "font_sizes": sizes,
        "roughness": mode(c["rough"], 0), "stroke": stroke, "stroke_width": mode(c["sw"], 2),
        "roundness": None if mode(c["round"], "sharp") == "sharp" else {"type": 3},
        "fill_style": mode(c["fillstyle"], "solid"),
        "arrowhead": mode(c["head"], "triangle_outline"), "elbowed": bool(mode(c["elbow"], True)),
        "canvas": mode(c["canvas"], "#ffffff"),
        "fills": fills or dict(FILLS), "tints": tints or dict(TINTS), "arrow_colors": acolors,
        "store_fills": stores,
    }


def main():
    args = sys.argv[1:]
    out = args[args.index("-o") + 1] if "-o" in args else "style.json"
    name = args[args.index("--name") + 1] if "--name" in args else None
    inputs = [a for i, a in enumerate(args) if not a.startswith("-") and (i == 0 or args[i - 1] not in ("-o", "--name"))]
    if not inputs:
        print(__doc__); sys.exit(2)
    paths = []
    for a in inputs:
        paths += glob.glob(os.path.join(a, "**", "*.excalidraw"), recursive=True) if os.path.isdir(a) else [a]
    prof = profile(paths)
    if name:
        prof["name"] = name
    json.dump(prof, open(out, "w", encoding="utf-8"), indent=1)
    m = prof["measured_from"]
    print(f"wrote {out} from {m['files']} files ({m['text']} texts, {m['shapes']} shapes, {m['arrows']} arrows)")
    print(f"  font {FONT_NAMES.get(prof['font'], prof['font'])}, sizes {prof['font_sizes']}, roughness {prof['roughness']}, "
          f"stroke {prof['stroke']} x{prof['stroke_width']}, corners {'sharp' if prof['roundness'] is None else 'rounded'}")
    print(f"  arrows {prof['arrowhead']}, elbowed {prof['elbowed']}; fills {prof['fills']}")
    print("  review it, then use:  build.py / lint.py / fix.py ... --style " + out)


if __name__ == "__main__":
    main()

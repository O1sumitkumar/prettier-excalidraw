#!/usr/bin/env python3
"""Render a rough SVG preview of a .excalidraw file so layout can be checked
without opening Excalidraw. Boxes, text, images and arrows only; good enough
to spot overlaps, misplaced labels and arrow routing.

Usage:
    python3 preview.py diagram.excalidraw out.svg [--square]
--square pads the canvas to a square so a quick-look thumbnail does not crop a
wide diagram. On macOS, rasterise with:
    qlmanage -t -s 2400 -o <dir> out.svg        -> <dir>/out.svg.png
Standard library only.
"""
import html, json, sys
from exstyle import bbox

FONT_CSS = {8: "'Comic Shanns', 'Comic Mono', monospace", 6: "'Nunito', sans-serif"}


def render_svg(d, square=False, fonts=None):
    """Return the SVG text for an Excalidraw document.
    fonts: {family-name: [woff2 bytes, ...]} to embed as @font-face (see export.py)."""
    els = [e for e in d["elements"] if not e.get("isDeleted")]
    files = d.get("files", {})
    xs0, ys0, xs1, ys1 = zip(*(bbox(e) for e in els))
    pad = 40
    minx, miny, maxx, maxy = min(xs0) - pad, min(ys0) - pad, max(xs1) + pad, max(ys1) + pad
    if square:
        w, h = maxx - minx, maxy - miny
        if w > h:
            miny -= (w - h) / 2; maxy += (w - h) / 2
        else:
            minx -= (h - w) / 2; maxx += (h - w) / 2
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
             f'viewBox="{minx} {miny} {maxx-minx} {maxy-miny}" width="{maxx-minx}" height="{maxy-miny}">',
             f'<rect x="{minx}" y="{miny}" width="{maxx-minx}" height="{maxy-miny}" fill="#fff"/>']
    for e in els:
        t = e["type"]; op = e.get("opacity", 100) / 100
        sc = e.get("strokeColor", "#1e1e1e"); sw = e.get("strokeWidth", 2)
        dash = {"dotted": f'stroke-dasharray="{sw*1.5} {sw*3}"', "dashed": f'stroke-dasharray="{sw*4} {sw*3}"'}.get(e.get("strokeStyle"), "")
        if t in ("rectangle", "ellipse", "diamond"):
            fill = e.get("backgroundColor", "transparent")
            fill = "none" if fill == "transparent" else fill
            if t == "rectangle":
                parts.append(f'<rect x="{e["x"]}" y="{e["y"]}" width="{e["width"]}" height="{e["height"]}" fill="{fill}" stroke="{sc}" stroke-width="{sw}" opacity="{op}" {dash}/>')
            elif t == "ellipse":
                parts.append(f'<ellipse cx="{e["x"]+e["width"]/2}" cy="{e["y"]+e["height"]/2}" rx="{e["width"]/2}" ry="{e["height"]/2}" fill="{fill}" stroke="{sc}" stroke-width="{sw}" opacity="{op}"/>')
            else:
                x, y, w, h = e["x"], e["y"], e["width"], e["height"]
                parts.append(f'<polygon points="{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}" fill="{fill}" stroke="{sc}" stroke-width="{sw}" opacity="{op}"/>')
        elif t == "text":
            fs = e.get("fontSize", 20); ff = FONT_CSS.get(e.get("fontFamily"), "monospace")
            lines = e["text"].split("\n"); lh = fs * e.get("lineHeight", 1.25)
            anchor = {"center": "middle", "right": "end"}.get(e.get("textAlign"), "start")
            ax = {"middle": e["x"] + e["width"] / 2, "end": e["x"] + e["width"]}.get(anchor, e["x"])
            longest = max(len(l) for l in lines) or 1
            for i, line in enumerate(lines):
                # force each line to the width Excalidraw stored, so the preview shows the real layout
                tl = e["width"] * len(line) / longest
                parts.append(f'<text xml:space="preserve" x="{ax}" y="{e["y"] + lh*i + fs*0.95}" font-size="{fs}" font-family="{ff}" fill="{sc}" text-anchor="{anchor}" opacity="{op}" textLength="{tl:.1f}" lengthAdjust="spacingAndGlyphs">{html.escape(line)}</text>')
        elif t == "image":
            f = files.get(e.get("fileId"))
            if f:
                parts.append(f'<image x="{e["x"]}" y="{e["y"]}" width="{e["width"]}" height="{e["height"]}" xlink:href="{f["dataURL"]}" preserveAspectRatio="none"/>')
            else:
                parts.append(f'<rect x="{e["x"]}" y="{e["y"]}" width="{e["width"]}" height="{e["height"]}" fill="#eee" stroke="#999"/>')
        elif t in ("arrow", "line", "freedraw"):
            pts = [(e["x"] + p[0], e["y"] + p[1]) for p in e.get("points", [])]
            if len(pts) < 2: continue
            fill = e.get("backgroundColor", "transparent") if t == "line" and len(pts) > 2 else "none"
            fill = "none" if fill == "transparent" else fill
            parts.append(f'<polyline points="{" ".join(f"{x},{y}" for x, y in pts)}" fill="{fill}" stroke="{sc}" stroke-width="{sw}" opacity="{op}" stroke-linejoin="round" {dash}/>')
            for key, idx, prev in (("endArrowhead", -1, -2), ("startArrowhead", 0, 1)):
                head = e.get(key)
                if head and t == "arrow":
                    (x1, y1), (x0, y0) = pts[idx], pts[prev]
                    import math
                    ang = math.atan2(y1 - y0, x1 - x0); L = 14 if sw <= 2 else 20
                    a1 = (x1 - L*math.cos(ang - 0.4), y1 - L*math.sin(ang - 0.4))
                    a2 = (x1 - L*math.cos(ang + 0.4), y1 - L*math.sin(ang + 0.4))
                    hf = "#fff" if "outline" in head else sc
                    if head in ("arrow",):
                        parts.append(f'<polyline points="{a1[0]},{a1[1]} {x1},{y1} {a2[0]},{a2[1]}" fill="none" stroke="{sc}" stroke-width="{sw}"/>')
                    else:
                        parts.append(f'<polygon points="{a1[0]},{a1[1]} {x1},{y1} {a2[0]},{a2[1]}" fill="{hf}" stroke="{sc}" stroke-width="{sw}"/>')
    parts.append("</svg>")
    if fonts:
        import base64
        faces = []
        for fam, blobs in fonts.items():
            for blob in blobs:
                faces.append(f"@font-face{{font-family:'{fam}';src:url(data:font/woff2;base64,"
                             f"{base64.b64encode(blob).decode()}) format('woff2');}}")
        parts.insert(1, "<style>" + "".join(faces) + "</style>")
    return "\n".join(parts)


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    src, out = sys.argv[1], sys.argv[2]
    square = "--square" in sys.argv
    d = json.load(open(src))
    open(out, "w").write(render_svg(d, square=square))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

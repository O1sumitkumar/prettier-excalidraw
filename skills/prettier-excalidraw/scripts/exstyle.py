"""Shared style constants for prettier-excalidraw scripts (stdlib only)."""

FONT_IDS = {"comic": 8, "nunito": 6}
FONT_NAMES = {8: "Comic Shanns", 6: "Nunito", 1: "Virgil", 2: "Helvetica", 3: "Cascadia",
              5: "Excalifont", 7: "Lilita One"}
# average glyph width as a fraction of fontSize (measured from reference diagrams)
CHAR_W = {8: 0.55, 6: 0.49}
LINE_H = 1.25
FONT_SIZES = [16, 20, 28]   # mutable: a style profile may replace the set

STROKE = "#1e1e1e"
ARROW_COLORS = {"black": "#1e1e1e", "red": "#e03131", "green": "#2f9e44", "blue": "#1971c2"}

# component box fills
FILLS = {
    "blue": "#a5d8ff", "yellow": "#ffec99", "green": "#b2f2bb", "red": "#ffc9c9",
    "purple": "#d0bfff", "orange": "#ffd8a8", "teal": "#96f2d7", "cyan": "#99e9f2",
    "grey": "#ced4da", "lightgrey": "#e9ecef", "white": "#ffffff", "none": "transparent",
}
# large region tints (one scale lighter)
TINTS = {
    "blue": "#e7f5ff", "teal": "#e6fcf5", "yellow": "#fff9db", "orange": "#fff4e6",
    "purple": "#f3f0ff", "red": "#fff5f5", "none": "transparent", "white": "#ffffff",
}
LIGHT_FILLS = set(FILLS.values()) | set(TINTS.values()) | {"#fff", "#ffffff", "transparent"}

ARROWHEADS = {"outline": "triangle_outline", "filled": "triangle", "arrow": "arrow", "bar": "bar",
              "dot": "dot", "circle": "circle", "none": None}

# The active style. Scripts read these at call time, so a loaded profile applies
# everywhere. Defaults are the measured house style.
STYLE = {
    "name": "house",
    "font": 8,                      # fontFamily id (8 Comic Shanns, 6 Nunito, 2 Helvetica, 3 Cascadia, 5 Excalifont)
    "font_sizes": FONT_SIZES,       # same list object
    "roughness": 0,
    "stroke": STROKE,
    "stroke_width": 2,
    "roundness": None,              # None = sharp corners, or {"type": 3} for rounded
    "fill_style": "solid",
    "arrowhead": "triangle_outline",
    "elbowed": True,
    "canvas": "#ffffff",
    "fills": FILLS,                 # same dict objects, updated in place by load_style
    "tints": TINTS,
    "arrow_colors": ARROW_COLORS,
    "store_fills": ["#ffc9c9"],
}


def size(which):
    """Default font sizes from the active profile: 'small', 'default', 'title'."""
    return {"small": FONT_SIZES[0], "default": FONT_SIZES[len(FONT_SIZES) // 2], "title": FONT_SIZES[-1]}[which]


def load_style(path):
    """Apply a style.json (written by profile.py or by hand) on top of the defaults."""
    import json
    d = json.load(open(path, encoding="utf-8"))
    for k in ("name", "font", "roughness", "stroke", "stroke_width", "roundness", "fill_style",
              "arrowhead", "elbowed", "canvas", "store_fills"):
        if k in d:
            STYLE[k] = d[k]
    if "font_sizes" in d:
        FONT_SIZES[:] = list(d["font_sizes"])
    for key, target in (("fills", FILLS), ("tints", TINTS), ("arrow_colors", ARROW_COLORS)):
        if key in d:
            target.clear(); target.update(d[key])
    LIGHT_FILLS.clear(); LIGHT_FILLS.update(set(FILLS.values()) | set(TINTS.values()) | {"#fff", "#ffffff", "transparent"})
    return STYLE


def style_from_argv(argv):
    """Honour `--style path` anywhere on a command line (and PRETTIER_EXCALIDRAW_STYLE)."""
    import os
    path = argv[argv.index("--style") + 1] if "--style" in argv else os.environ.get("PRETTIER_EXCALIDRAW_STYLE")
    if path:
        load_style(path)
    return path


def is_light(hexcolor: str) -> bool:
    """True if a fill is light enough to carry #1e1e1e text."""
    if not hexcolor or hexcolor == "transparent":
        return True
    h = hexcolor.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return True
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (0.299 * r + 0.587 * g + 0.114 * b) > 150


def bbox(e):
    if e["type"] in ("arrow", "line", "freedraw"):
        pts = e.get("points") or [[0, 0]]
        xs = [e["x"] + p[0] for p in pts]
        ys = [e["y"] + p[1] for p in pts]
        return min(xs), min(ys), max(xs), max(ys)
    return e["x"], e["y"], e["x"] + e["width"], e["y"] + e["height"]


def inside(a, b, tol=4):
    return a[0] >= b[0] - tol and a[1] >= b[1] - tol and a[2] <= b[2] + tol and a[3] <= b[3] + tol


def overlap(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def area(b):
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _rgb(hexcolor):
    h = hexcolor.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(hexcolor):
    """WCAG relative luminance, 0 (black) to 1 (white)."""
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = _rgb(hexcolor)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(fg, bg):
    """WCAG contrast ratio between two hex colours (1 = identical, 21 = black on white)."""
    l1, l2 = luminance(fg), luminance(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


ICON_MIN_CONTRAST = 3.0   # WCAG threshold for graphics


def darken_to_contrast(fg, bg, target=ICON_MIN_CONTRAST):
    """Scale a colour towards black until it reaches the target contrast on bg.
    Returns the (possibly unchanged) hex colour."""
    r, g, b = _rgb(fg)
    f = 1.0
    while contrast("#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f)), bg) < target and f > 0.05:
        f -= 0.05
    return "#%02x%02x%02x" % (int(r * f), int(g * f), int(b * f))

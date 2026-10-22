#!/usr/bin/env python3
"""Fetch brand icons from Simple Icons with the brand colour applied.

Usage:
    python3 icons.py fetch <slug> [<slug>...] [-o icons/] [--color #hex]
    python3 icons.py search <words>

`fetch` tries cdn.simpleicons.org, falls back to the npm package on jsDelivr (the CDN
answers non-browser clients with a bot challenge), injects the brand colour as a root
`fill` when the file has none (the jsDelivr copies have none), validates the result and
writes <slug>.svg. `--color` forces a colour for every slug given.
`search` lists icons whose title or slug contains the words, so "fly" finds flydotio.
The icon catalogue is cached in ~/.cache/prettier-excalidraw/simple-icons.json.
Standard library only.
"""
import json, os, re, sys, urllib.request

CDN = "https://cdn.simpleicons.org/{}"
NPM = "https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{}.svg"
DATA = "https://cdn.jsdelivr.net/npm/simple-icons@latest/_data/simple-icons.json"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "prettier-excalidraw", "simple-icons.json")
UA = {"User-Agent": "Mozilla/5.0 (prettier-excalidraw icons.py)"}


def _get(url, timeout=15):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read()


def title_to_slug(title):
    """Simple Icons' slug rules: lowercase, +→plus, .→dot, &→and, đ→d, ħ→h, ı→i, ĸ→k,
    ŀ→l, ł→l, ß→ss, ŧ→t, strip accents and anything not a-z0-9."""
    import unicodedata
    t = title.lower()
    for a, b in (("+", "plus"), (".", "dot"), ("&", "and"), ("đ", "d"), ("ħ", "h"), ("ı", "i"), ("ĸ", "k"),
                 ("ŀ", "l"), ("ł", "l"), ("ß", "ss"), ("ŧ", "t")):
        t = t.replace(a, b)
    t = unicodedata.normalize("NFD", t)
    return re.sub(r"[^a-z0-9]", "", t)


def catalogue():
    """[{title, slug, hex}] from cache or the network; [] when offline."""
    if not os.path.exists(CACHE):
        try:
            os.makedirs(os.path.dirname(CACHE), exist_ok=True)
            open(CACHE, "wb").write(_get(DATA, 30))
        except Exception:
            return []
    d = json.load(open(CACHE, encoding="utf-8"))
    d = d.get("icons", d) if isinstance(d, dict) else d
    return [{"title": i["title"], "slug": i.get("slug") or title_to_slug(i["title"]), "hex": "#" + i["hex"]} for i in d]


def inject_fill(svg, color):
    """Put fill="color" on the root <svg> if it has no fill; replace it if it has one."""
    if re.search(r'<svg\b[^>]*?\sfill=', svg):
        return re.sub(r'(<svg\b[^>]*?\sfill=)(["\'])#?[0-9a-fA-F]{3,8}\2', lambda m: f'{m.group(1)}"{color}"', svg, count=1)
    return svg.replace("<svg", f'<svg fill="{color}"', 1)


def fetch(slug, color=None):
    """Return SVG text for a slug, coloured; raises SystemExit with a reason when it cannot."""
    svg = None
    for url in (CDN.format(slug), NPM.format(slug)):
        try:
            data = _get(url)
        except Exception:
            continue
        text = data.decode("utf-8", "ignore").lstrip("﻿ \t\r\n")
        if text.startswith("<svg") or text.startswith("<?xml"):
            svg = text
            break
    if svg is None:
        hint = ""
        near = [i for i in catalogue() if slug in i["slug"] or slug in i["title"].lower()][:5]
        if near:
            hint = "; similar: " + ", ".join(f"{i['slug']} ({i['title']})" for i in near)
        raise SystemExit(f"no icon for slug '{slug}'{hint}")
    if color is None:
        entry = next((i for i in catalogue() if i["slug"] == slug), None)
        color = entry["hex"] if entry else None
    if color:
        svg = inject_fill(svg, color if color.startswith("#") else "#" + color)
    return svg


def main():
    args = sys.argv[1:]
    if not args or args[0] not in ("fetch", "search"):
        print(__doc__); sys.exit(2)
    if args[0] == "search":
        q = " ".join(args[1:]).lower()
        hits = [i for i in catalogue() if q in i["title"].lower() or q in i["slug"]]
        for i in hits[:30]:
            print(f"{i['slug']:28s} {i['title']:36s} {i['hex']}")
        if not hits:
            print("no matches (catalogue empty? check network)"); sys.exit(1)
        return
    out = args[args.index("-o") + 1] if "-o" in args else "icons"
    color = args[args.index("--color") + 1] if "--color" in args else None
    slugs = [a for i, a in enumerate(args[1:], 1) if not a.startswith("-") and args[i - 1] not in ("-o", "--color")]
    os.makedirs(out, exist_ok=True)
    for slug in slugs:
        svg = fetch(slug, color)
        path = os.path.join(out, f"{slug}.svg")
        open(path, "w", encoding="utf-8").write(svg)
        m = re.search(r'fill="(#[0-9a-fA-F]+)"', svg)
        print(f"wrote {path} ({m.group(1) if m else 'no colour'})")


if __name__ == "__main__":
    main()

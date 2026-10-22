#!/usr/bin/env python3
"""Export a .excalidraw diagram to SVG or PNG in the prettier-excalidraw style.

Usage:
    python3 export.py diagram.excalidraw out.svg
    python3 export.py diagram.excalidraw out.png [--scale 2] [--no-fonts]

SVG: exact layout, with the real Comic Shanns / Nunito fonts embedded as data URIs
(fetched once from the Excalidraw repository and cached in ~/.cache/prettier-excalidraw;
--no-fonts or no network falls back to a system font stack).
PNG: the SVG rasterised with headless Chrome / Chromium / Edge when one is installed,
otherwise macOS quick-look. --scale sets the device pixel ratio (default 2).
Standard library only.
"""
import glob, json, os, platform, shutil, subprocess, sys, tempfile, urllib.request
from preview import render_svg

FONT_DIRS = {"Comic Shanns": "ComicShanns", "Nunito": "Nunito"}
API = "https://api.github.com/repos/excalidraw/excalidraw/contents/packages/excalidraw/fonts/{}"
RAW = "https://raw.githubusercontent.com/excalidraw/excalidraw/master/packages/excalidraw/fonts/{}/{}"
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "prettier-excalidraw", "fonts")


def fetch_fonts(timeout=15):
    """Return {family: [woff2 bytes]} from cache or the Excalidraw repo; {} if unavailable."""
    out = {}
    for family, folder in FONT_DIRS.items():
        cdir = os.path.join(CACHE, folder)
        files = sorted(glob.glob(os.path.join(cdir, "*.woff2")))
        if not files:
            try:
                with urllib.request.urlopen(API.format(folder), timeout=timeout) as r:
                    names = [e["name"] for e in json.load(r) if e["name"].endswith(".woff2")]
                os.makedirs(cdir, exist_ok=True)
                for n in names:
                    with urllib.request.urlopen(RAW.format(folder, n), timeout=timeout) as r:
                        open(os.path.join(cdir, n), "wb").write(r.read())
                files = sorted(glob.glob(os.path.join(cdir, "*.woff2")))
            except Exception as ex:  # offline, rate limited, moved
                print(f"note: could not fetch {family} ({ex.__class__.__name__}); using a system font", file=sys.stderr)
                continue
        out[family] = [open(f, "rb").read() for f in files]
    return out


def find_chrome():
    cands = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge",
             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
             "/Applications/Chromium.app/Contents/MacOS/Chromium",
             "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
             r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]
    for c in cands:
        p = shutil.which(c) if not os.path.isabs(c) else (c if os.path.exists(c) else None)
        if p:
            return p
    return None


def svg_size(svg):
    import re
    w = float(re.search(r'\swidth="([\d.]+)"', svg).group(1))
    h = float(re.search(r'\sheight="([\d.]+)"', svg).group(1))
    return int(round(w)), int(round(h))


def to_png(svg, out, scale=2):
    w, h = svg_size(svg)
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "d.svg")
        open(src, "w", encoding="utf-8").write(svg)
        chrome = find_chrome()
        if chrome:
            # a throwaway profile keeps this independent of a Chrome window that is already open
            subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            f"--user-data-dir={os.path.join(td, 'profile')}",
                            f"--force-device-scale-factor={scale}", f"--screenshot={os.path.abspath(out)}",
                            f"--window-size={w},{h}", "file://" + src],
                           check=True, timeout=90, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "chrome"
        if platform.system() == "Darwin" and shutil.which("qlmanage"):
            # quick-look only makes square thumbnails: render a padded square, then crop back
            side = max(w, h)
            sq = svg.replace(f'width="{w}"', f'width="{side}"', 1).replace(f'height="{h}"', f'height="{side}"', 1)
            import re
            vb = re.search(r'viewBox="([\d.\-]+) ([\d.\-]+) ([\d.]+) ([\d.]+)"', sq)
            x0, y0, vw, vh = map(float, vb.groups())
            sq = sq.replace(vb.group(0), f'viewBox="{x0 - (side - vw) / 2} {y0 - (side - vh) / 2} {side} {side}"', 1)
            open(src, "w", encoding="utf-8").write(sq)
            px = int(side * scale)
            subprocess.run(["qlmanage", "-t", "-s", str(px), "-o", td, src], check=True, timeout=90,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            thumb = src + ".png"
            subprocess.run(["sips", "-c", str(int(h * scale)), str(int(w * scale)), thumb, "--out", os.path.abspath(out)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "quicklook"
    raise SystemExit("no renderer found: install Chrome/Chromium, or export to .svg instead")


def export(src, out, scale=2, fonts=True):
    doc = json.load(open(src, encoding="utf-8"))
    svg = render_svg(doc, fonts=fetch_fonts() if fonts else None)
    if out.lower().endswith(".svg"):
        open(out, "w", encoding="utf-8").write(svg)
        return "svg"
    if out.lower().endswith(".png"):
        return to_png(svg, out, scale)
    raise SystemExit("output must end with .svg or .png")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__); sys.exit(2)
    scale = float(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 2
    how = export(args[0], args[1], scale=scale, fonts="--no-fonts" not in sys.argv)
    print(f"wrote {args[1]} ({how})")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Export a .excalidraw diagram to SVG, PNG or an animated HTML page.

Usage:
    python3 export.py diagram.excalidraw out.svg
    python3 export.py diagram.excalidraw out.png [--scale 2] [--no-fonts]
    python3 export.py diagram.excalidraw out.html [--spec spec.json] [--no-fonts]

SVG: exact layout, with the real Comic Shanns / Nunito fonts embedded as data URIs
(fetched once from the Excalidraw repository and cached in ~/.cache/prettier-excalidraw;
--no-fonts or no network falls back to a system font stack).
PNG: the SVG rasterised with headless Chrome / Chromium / Edge when one is installed,
otherwise macOS quick-look. --scale sets the device pixel ratio (default 2).
HTML: the same SVG in one self-contained page where arrows flow in their direction,
hovering a shape lights up its connections, a button plays a request path one arrow
at a time, and shapes with a link open it. Nothing is loaded from the network when
the page is viewed. --spec reads `paths` from the spec for named play buttons.
Standard library only.
"""
import glob, html as _html, json, os, platform, re, shutil, subprocess, sys, tempfile, urllib.request
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


HTML_CSS = """
body{margin:0;min-height:100vh;display:flex;flex-direction:column;background:#f8f9fa;color:#1e1e1e;font-family:'Nunito',system-ui,sans-serif}
.bar{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;padding:10px 16px;background:#fff;border-bottom:1px solid #dee2e6}
.bar button{font:inherit;font-size:14px;padding:5px 12px;border:1px solid #868e96;border-radius:4px;background:#fff;color:#1e1e1e;cursor:pointer}
.bar button.on{background:#1e1e1e;color:#fff;border-color:#1e1e1e}
.bar .hint{color:#868e96;font-size:13px}
.bar .title{font-weight:700;margin-right:8px}
/* the drawing sits in the middle of the screen, as large as the window allows */
main{flex:1;display:flex;align-items:center;justify-content:center;padding:24px;box-sizing:border-box}
svg{display:block;width:auto;height:auto;max-width:100%;max-height:calc(100vh - 110px);background:#fff;border-radius:10px;box-shadow:0 4px 24px rgba(0,0,0,.08)}
/* flow: dashes travel along the line in the arrow's direction; heads stay solid */
@keyframes flow{to{stroke-dashoffset:-36}}
svg.flowing .arrow:not([data-flow=off]) .line{stroke-dasharray:14 10;animation:flow 1s linear infinite}
/* a double-headed arrow claims no direction: its dashes go back and forth instead */
svg.flowing .arrow[data-bidirectional] .line{animation-direction:alternate;animation-duration:1.6s}
/* hover: the shape lifts, what it touches stays, the rest fades */
.box,.region,.image{transition:opacity .15s}
.box:hover>rect,.box:hover>ellipse,.box:hover>polygon{filter:brightness(.92);stroke-width:3}
[data-link]{cursor:pointer}
svg.focus .arrow:not(.lit){opacity:.15}
svg.focus .box:not(.lit),svg.focus .image:not(.lit),svg.focus .label:not(.lit){opacity:.3}
.arrow.lit .line{stroke-width:3.5}
/* play: one arrow at a time */
.arrow.step .line{stroke:#e03131;stroke-width:4;stroke-dasharray:14 10;animation:flow .6s linear infinite}
.arrow.step polygon{stroke:#e03131}
svg.playing .arrow:not(.step):not(.done):not(.choice){opacity:.2}
/* explore: play from any box; at a fork the candidate arrows glow and wait for a pick */
svg.explore .box,svg.explore .image,.arrow.choice{cursor:pointer}
.arrow.choice .line{stroke:#e03131;stroke-width:3.5;stroke-dasharray:4 6}
.arrow.choice polygon{stroke:#e03131}
.badges g{cursor:pointer}.badges circle{fill:#e03131;stroke:#fff;stroke-width:2}
.badges text{fill:#fff;font:700 15px 'Nunito',system-ui,sans-serif;text-anchor:middle;pointer-events:none}
.bar .status{color:#e03131;font-size:13px}
@media (prefers-reduced-motion:reduce){svg.flowing .arrow .line,.arrow.step .line{animation:none}}
"""

HTML_JS = """
const svg=document.querySelector('svg'),bar=document.querySelector('.bar');
const arrows=[...svg.querySelectorAll('g.arrow')],shapes=[...svg.querySelectorAll('g.box,g.region,g.image')];
const labels=[...svg.querySelectorAll('g.label')],byId=id=>svg.querySelector('g[id="'+CSS.escape(id)+'"]');
const paths=JSON.parse(document.getElementById('paths').textContent);
if(!matchMedia('(prefers-reduced-motion: reduce)').matches)svg.classList.add('flowing');
const flowBtn=document.getElementById('flow');flowBtn.classList.toggle('on',svg.classList.contains('flowing'));
flowBtn.onclick=()=>{svg.classList.toggle('flowing');flowBtn.classList.toggle('on')};
function light(el){el&&el.classList.add('lit')}
shapes.forEach(s=>{
  s.addEventListener('mouseenter',()=>{svg.classList.add('focus');light(s);
    labels.forEach(l=>{if(l.dataset.for===s.id)light(l)});
    arrows.forEach(a=>{if(a.dataset.from===s.id||a.dataset.to===s.id){light(a);
      const other=byId(a.dataset.from===s.id?a.dataset.to:a.dataset.from);light(other);
      labels.forEach(l=>{if(other&&l.dataset.for===other.id)light(l)})}})});
  s.addEventListener('mouseleave',()=>{svg.classList.remove('focus');svg.querySelectorAll('.lit').forEach(x=>x.classList.remove('lit'))});
  s.addEventListener('click',()=>{
    if(walk&&walk.choices){const i=walk.choices.findIndex(a=>other(a,walk.cur)===s.id);if(i>=0)return pick(i)}
    if(svg.classList.contains('explore'))return explore(s.id);
    if(s.dataset.link)window.open(s.dataset.link,'_blank','noopener')});
});
function autoPath(){const inc=new Set(arrows.map(a=>a.dataset.to));
  let cur=(shapes.find(s=>s.classList.contains('box')&&!inc.has(s.id))||shapes[0]||{}).id,seen=new Set(),out=[];
  while(cur){const nxt=arrows.find(a=>a.dataset.from===cur&&!seen.has(a.id));if(!nxt)break;seen.add(nxt.id);out.push(nxt);cur=nxt.dataset.to}
  return out}
function namedPath(ids){const out=[];for(let i=0;i+1<ids.length;i++){const a=ids[i],b=ids[i+1];
  const hit=arrows.find(x=>(x.dataset.from===a&&x.dataset.to===b)||(x.dataset.bidirectional&&x.dataset.from===b&&x.dataset.to===a));
  if(hit)out.push(hit);else console.warn('no arrow between',a,'and',b)}return out}
/* playback: named paths walk a list; explore walks the drawing and pauses at forks */
let timer=null,walk=null;
const status=document.createElement('span');status.className='status';bar.insertBefore(status,bar.querySelector('.hint'));
function reset(){if(timer){clearTimeout(timer);timer=null}walk=null;status.textContent='';
  arrows.forEach(a=>a.classList.remove('step','done','choice'));const b=svg.querySelector('g.badges');if(b)b.remove();svg.classList.remove('playing')}
function finish(){timer=setTimeout(()=>{timer=null;walk=null;svg.classList.remove('playing');arrows.forEach(a=>a.classList.remove('done'))},800)}
function play(seq){reset();if(!seq.length)return;svg.classList.add('playing');let i=0;
  const tick=()=>{if(i>0)seq[i-1].classList.replace('step','done');if(i>=seq.length)return finish();seq[i].classList.add('step');i++;timer=setTimeout(tick,700)};
  tick()}
const other=(a,id)=>a.dataset.from===id?a.dataset.to:a.dataset.from;
const name=id=>{const l=labels.find(l=>l.dataset.for===id),t=l&&l.querySelector('text');return t?t.textContent:id};
function outgoing(id,visited){return arrows.filter(a=>!visited.has(a.id)&&(a.dataset.from===id||(a.dataset.bidirectional&&a.dataset.to===id)))}
function explore(id){reset();if(!byId(id))return;svg.classList.add('playing');walk={cur:id,visited:new Set(),last:null,choices:null};stepWalk()}
function stepWalk(){const w=walk;if(!w)return;if(w.last)w.last.classList.replace('step','done');
  const opts=outgoing(w.cur,w.visited);
  if(!opts.length){status.textContent='';return finish()}
  if(opts.length===1)return go(opts[0]);
  w.choices=opts;opts.forEach((a,i)=>{a.classList.add('choice');badge(a,i)});
  status.textContent=opts.length+' ways out of '+name(w.cur)+': pick '+opts.map((a,i)=>KEYS[i]).join(', ')+' (click or type the letter)'}
function go(a){const w=walk;w.choices=null;arrows.forEach(x=>x.classList.remove('choice'));const b=svg.querySelector('g.badges');if(b)b.remove();
  a.classList.add('step');w.visited.add(a.id);w.last=a;w.cur=other(a,w.cur);status.textContent='';timer=setTimeout(stepWalk,700)}
function pick(i){if(walk&&walk.choices&&walk.choices[i])go(walk.choices[i])}
const NS='http://www.w3.org/2000/svg',KEYS='ABCDEFGHIJKLMNOPQRSTUVWXYZ';
function mid(a){const pts=a.querySelector('.line').getAttribute('points').trim().split(/\\s+/).map(p=>p.split(',').map(Number));
  let best=pts[0],bl=-1;for(let i=0;i+1<pts.length;i++){const [x0,y0]=pts[i],[x1,y1]=pts[i+1],l=Math.hypot(x1-x0,y1-y0);if(l>bl){bl=l;best=[(x0+x1)/2,(y0+y1)/2]}}return best}
function badge(a,i){let g=svg.querySelector('g.badges');if(!g){g=document.createElementNS(NS,'g');g.setAttribute('class','badges');svg.appendChild(g)}
  const [x,y]=mid(a),c=document.createElementNS(NS,'g');
  const circle=document.createElementNS(NS,'circle');circle.setAttribute('cx',x);circle.setAttribute('cy',y);circle.setAttribute('r',13);
  const t=document.createElementNS(NS,'text');t.setAttribute('x',x);t.setAttribute('y',y+5);t.textContent=KEYS[i]||'?';
  c.append(circle,t);c.onclick=()=>pick(i);g.appendChild(c)}
arrows.forEach(a=>a.addEventListener('click',()=>{if(walk&&walk.choices){const i=walk.choices.indexOf(a);if(i>=0)pick(i)}}));
document.addEventListener('keydown',e=>{if(e.key==='Escape')return reset();if(e.key.length===1){const i=KEYS.indexOf(e.key.toUpperCase());if(i>=0)pick(i)}});
const names=Object.keys(paths),hint=bar.querySelector('.hint');
if(names.length){names.forEach(n=>{const b=document.createElement('button');b.textContent='play: '+n;b.onclick=()=>play(namedPath(paths[n]));bar.insertBefore(b,status)})}
else if(arrows.length){const b=document.createElement('button');b.textContent='play request path';b.onclick=()=>play(autoPath());bar.insertBefore(b,status)}
if(arrows.length){const b=document.createElement('button');b.id='explore';b.textContent='explore';
  b.onclick=()=>{const on=svg.classList.toggle('explore');b.classList.toggle('on',on);if(!on)reset();
    hint.textContent=on?'click a box to play from it; where it forks, the lettered badges are the ways out':hint.dataset.base};
  hint.dataset.base=hint.textContent;flowBtn.after(b)}
const q=new URLSearchParams(location.search);
if(q.get('explore')){svg.classList.add('explore');const b=document.getElementById('explore');if(b)b.classList.add('on');explore(q.get('explore'))}
"""


def to_html(svg, title="diagram", paths=None):
    """Wrap a grouped SVG (render_svg(..., groups=True)) in a self-contained page."""
    paths = {k: list(v) for k, v in (paths or {}).items()}
    hint = "hover a shape to see its connections"
    if any("data-link=" in line for line in svg.split("\n")):
        hint += " · click a linked shape to open it"
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{_html.escape(title)}</title><style>{HTML_CSS}</style></head>\n<body>\n"
        f"<div class=\"bar\"><span class=\"title\">{_html.escape(title)}</span>"
        f"<button id=\"flow\">arrows flow</button><span class=\"hint\">{hint}</span></div>\n"
        f"<main>\n{svg}\n</main>\n"
        f"<script id=\"paths\" type=\"application/json\">{json.dumps(paths)}</script>\n"
        f"<script>{HTML_JS}</script>\n</body></html>\n"
    )


def export(src, out, scale=2, fonts=True, paths=None):
    doc = json.load(open(src, encoding="utf-8"))
    kind = os.path.splitext(out)[1].lower()
    if kind == ".html":
        svg = render_svg(doc, fonts=fetch_fonts() if fonts else None, groups=True)
        title = os.path.splitext(os.path.basename(src))[0]
        open(out, "w", encoding="utf-8").write(to_html(svg, title=title, paths=paths))
        return "html"
    svg = render_svg(doc, fonts=fetch_fonts() if fonts else None)
    if kind == ".svg":
        open(out, "w", encoding="utf-8").write(svg)
        return "svg"
    if kind == ".png":
        return to_png(svg, out, scale)
    raise SystemExit("output must end with .svg, .png or .html")


def paths_from_spec(spec_path):
    """The `paths` map of a spec ({name: [ids...]}), validated; {} when absent."""
    spec = json.load(open(spec_path, encoding="utf-8"))
    paths = spec.get("paths") or {}
    if not isinstance(paths, dict) or any(not isinstance(v, list) or len(v) < 2 for v in paths.values()):
        raise SystemExit("paths must be {name: [id, id, ...]} with at least two ids per path")
    return paths


def main():
    argv = sys.argv[1:]
    opts = {}
    for flag in ("--scale", "--spec"):
        if flag in argv:
            i = argv.index(flag); opts[flag] = argv[i + 1]; del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__); sys.exit(2)
    paths = paths_from_spec(opts["--spec"]) if "--spec" in opts else None
    how = export(args[0], args[1], scale=float(opts.get("--scale", 2)), fonts="--no-fonts" not in argv, paths=paths)
    print(f"wrote {args[1]} ({how})")


if __name__ == "__main__":
    main()

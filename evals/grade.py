#!/usr/bin/env python3
"""Grade eval outputs for prettier-excalidraw. Usage: grade.py <iteration-dir>"""
import json, os, sys, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "prettier-excalidraw", "scripts"))
from exstyle import bbox, inside, overlap, area, is_light
from lint import icon_groups

def load(p):
    d = json.load(open(p, encoding="utf-8")); return d, [e for e in d["elements"] if not e.get("isDeleted")]

def texts(els): return [e["text"].lower() for e in els if e["type"] == "text"]
def has_label(els, *words):
    t = " ".join(texts(els)); return all(w in t for w in words)

def one_font(els):
    fams = {e["fontFamily"] for e in els if e["type"] == "text"}
    return len(fams) == 1, f"fontFamily set: {sorted(fams)}"

def consistent_heads(els):
    heads = {e.get("endArrowhead") for e in els if e["type"] == "arrow" and e.get("endArrowhead")}
    ok = len(heads) == 1 and next(iter(heads)) in ("triangle", "triangle_outline")
    return ok, f"endArrowhead set: {sorted(heads)}"

def roughness_zero(els):
    icons = icon_groups(els)
    bad = [e["id"] for e in els if e["type"] in ("rectangle","ellipse","diamond","arrow","line","text")
           and e.get("roughness", 0) != 0 and not any(g in icons for g in e.get("groupIds", []))]
    return not bad, f"{len(bad)} non-icon elements with roughness != 0"

def no_hidden_arrows(els):
    idx = {e["id"]: i for i, e in enumerate(els)}
    rects = [e for e in els if e["type"] == "rectangle" and e.get("backgroundColor") not in (None, "transparent")]
    bad = 0
    for e in els:
        if e["type"] != "arrow" or not e.get("endArrowhead"): continue
        for r in rects:
            if idx[r["id"]] > idx[e["id"]] and overlap(bbox(e), bbox(r)) and area(bbox(r)) > 2000: bad += 1; break
    return bad == 0, f"{bad} arrows drawn before a filled box they cross"

def children_after_parents(els):
    idx = {e["id"]: i for i, e in enumerate(els)}
    rects = [e for e in els if e["type"] == "rectangle" and e.get("backgroundColor") not in (None, "transparent")]
    bad = sum(1 for c in rects for p in rects if p is not c and inside(bbox(c), bbox(p)) and area(bbox(p)) > area(bbox(c))*1.1 and idx[p["id"]] > idx[c["id"]])
    return bad == 0, f"{bad} child boxes drawn before their container"

def light_fills(els):
    byid = {e["id"]: e for e in els}
    fills = set(); dark = 0
    for e in els:
        if e["type"] in ("rectangle","ellipse","diamond") and e.get("backgroundColor") not in (None,"transparent"):
            fills.add(e["backgroundColor"])
            if any(b.get("type")=="text" for b in e.get("boundElements") or []) and not is_light(e["backgroundColor"]): dark += 1
    from exstyle import TINTS
    comp = fills - set(TINTS.values())
    return dark == 0 and 2 <= len(comp) <= 8, f"{len(comp)} distinct component fills (+{len(fills)-len(comp)} region tints), {dark} dark fills behind text"

def has_image(els, d):
    n = sum(1 for e in els if e["type"] == "image" and e.get("fileId") in d.get("files", {}))
    return n >= 1, f"{n} embedded images"

def container_of(els, words):
    """a rectangle that contains boxes whose bound text includes each word"""
    byid = {e["id"]: e for e in els}
    label_box = {}
    for e in els:
        if e["type"] == "text" and e.get("containerId") in byid:
            label_box[e["text"].lower()] = byid[e["containerId"]]
    targets = []
    for w in words:
        m = [b for t, b in label_box.items() if w in t]
        if not m: return False, f"no labelled box for '{w}'"
        targets.append(m[0])
    for r in els:
        if r["type"] == "rectangle" and all(inside(bbox(t), bbox(r)) and r is not t for t in targets):
            return True, f"container {r['id']} holds {words}"
    return False, f"no single rectangle contains {words}"

def stacked_layers(els, n=3):
    cands = [e for e in els if e["type"] == "rectangle" and e["width"] >= 500 and e["height"] >= 100]
    # keep those that contain >=3 labelled boxes
    byid = {e["id"]: e for e in els}
    boxes = [byid[t["containerId"]] for t in els if t["type"]=="text" and t.get("containerId") in byid]
    layers = [c for c in cands if sum(1 for b in boxes if b is not c and inside(bbox(b), bbox(c))) >= 3]
    # drop containers that contain other layer containers
    layers = [c for c in layers if not any(o is not c and inside(bbox(o), bbox(c)) for o in layers)]
    layers.sort(key=lambda e: e["y"])
    ok = len(layers) >= n and all(layers[i]["y"] + layers[i]["height"] <= layers[i+1]["y"] + 5 for i in range(len(layers)-1))
    tints = {l.get("backgroundColor") for l in layers}
    return ok, f"{len(layers)} stacked layer containers, tints {sorted(map(str,tints))}", layers

def grade(eval_name, run_dir, inputs_dir):
    exp = []
    def E(text, res):
        ok, ev = res[0], res[1]; exp.append({"text": text, "passed": bool(ok), "evidence": ev})
    out = os.path.join(run_dir, "outputs")
    if eval_name.startswith("eval-0"):
        p = os.path.join(out, "ecommerce.excalidraw")
        if not os.path.exists(p): return [{"text":"ecommerce.excalidraw exists and is valid","passed":False,"evidence":"missing"}]
        try: d, els = load(p)
        except Exception as ex: return [{"text":"ecommerce.excalidraw exists and is valid","passed":False,"evidence":str(ex)}]
        E("ecommerce.excalidraw exists and is valid Excalidraw JSON", (d.get("type")=="excalidraw" and len(els)>5, f"{len(els)} elements"))
        E("all required components labelled (ingress, orders, catalog, postgres, kafka, notification, sendgrid)", (has_label(els,"ingress","orders","catalog","postgres","kafka","notification","sendgrid"), " | ".join(texts(els))[:300]))
        E("kubernetes workloads grouped in one container (ingress, orders, catalog, notification)", container_of(els, ["ingress","orders","catalog","notification"]))
        E("single font family across all text", one_font(els))
        E("all arrowheads the same triangle style", consistent_heads(els))
        E("roughness 0 on all non-icon elements (not sketchy)", roughness_zero(els))
        E("no arrow hidden behind a filled box (arrows later in z-order)", no_hidden_arrows(els))
        E("containers drawn before their children", children_after_parents(els))
        E("light colour-coded fills, 2-8 distinct, none dark behind text", light_fills(els))
        E("at least one embedded logo image", has_image(els, d))
    elif eval_name.startswith("eval-1"):
        p = os.path.join(out, "idp-flow-clean.excalidraw"); src = os.path.join(inputs_dir, "idp-flow.excalidraw")
        if not os.path.exists(p): return [{"text":"idp-flow-clean.excalidraw exists","passed":False,"evidence":"missing"}]
        try: d, els = load(p); d0, els0 = load(src)
        except Exception as ex: return [{"text":"idp-flow-clean.excalidraw exists and is valid","passed":False,"evidence":str(ex)}]
        E("idp-flow-clean.excalidraw exists and is valid", (d.get("type")=="excalidraw", f"{len(els)} elements"))
        E("same element count as input (nothing dropped or added)", (len(els)==len(els0), f"{len(els)} vs {len(els0)}"))
        byid = {e["id"]: e for e in els}
        moved = [e["id"] for e in els0 if e["type"] not in ("text","arrow") and (e["id"] not in byid or abs(byid[e["id"]]["x"]-e["x"])>0.5 or abs(byid[e["id"]]["y"]-e["y"])>0.5)]
        E("no shape moved (same ids, same x/y; labels may be re-measured)", (not moved, f"{len(moved)} shapes moved or re-identified"))
        E("single font family across all text", one_font(els))
        E("all arrowheads the same triangle style", consistent_heads(els))
        E("roughness 0 on all non-icon elements", roughness_zero(els))
        shp = [e for e in els if e["type"] in ("rectangle","ellipse","diamond")]
        E("no hachure / cross-hatch fills on shapes", (not any(e.get("fillStyle") in ("hachure","cross-hatch") for e in shp), "fillStyles: " + str({e.get("fillStyle") for e in shp})))
        E("notes.md written", (os.path.exists(os.path.join(out,"notes.md")), "present" if os.path.exists(os.path.join(out,"notes.md")) else "missing"))
    else:
        p = os.path.join(out, "platform.excalidraw")
        if not os.path.exists(p): return [{"text":"platform.excalidraw exists","passed":False,"evidence":"missing"}]
        try: d, els = load(p)
        except Exception as ex: return [{"text":"platform.excalidraw exists and is valid","passed":False,"evidence":str(ex)}]
        E("platform.excalidraw exists and is valid", (d.get("type")=="excalidraw" and len(els)>5, f"{len(els)} elements"))
        E("all 12 components labelled", (has_label(els,"portal","cli","docs","template","ci","secret","observab","identity","kubernetes","postgres","storage","queue"), " | ".join(texts(els))[:300]))
        ok, ev, layers = stacked_layers(els)
        E("three full-width layers stacked vertically, each containing >= 3 labelled boxes", (ok, ev))
        E("layers visually distinct (different tint or component fill per layer)", (ok and len({l.get("backgroundColor") for l in layers[:3]}) == 3, ev))
        E("single font family across all text", one_font(els))
        E("roughness 0 on all non-icon elements", roughness_zero(els))
        E("no arrow hidden behind a filled box", no_hidden_arrows(els))
        E("containers drawn before their children", children_after_parents(els))
        E("light fills, none dark behind text", light_fills(els))
        E("at least one embedded logo image", has_image(els, d))
    return exp

if __name__ == "__main__":
    it = sys.argv[1]
    for ev in sorted(glob.glob(os.path.join(it, "eval-*"))):
        name = os.path.basename(ev)
        for rd in sorted(glob.glob(os.path.join(ev, "*_skill", "run-*"))):
            run = os.path.basename(os.path.dirname(rd))
            exp = grade(name, rd, os.path.join(it, "inputs"))
            n = sum(e["passed"] for e in exp)
            json.dump({"expectations": exp, "summary": {"passed": n, "failed": len(exp) - n, "total": len(exp),
                       "pass_rate": round(n / len(exp), 3) if exp else 0.0}},
                      open(os.path.join(rd, "grading.json"), "w", encoding="utf-8"), indent=1)
            print(f"{name:28s} {run:14s} {n}/{len(exp)}")
            for e in exp:
                if not e["passed"]: print(f"     FAIL {e['text']}  -- {e['evidence'][:120]}")

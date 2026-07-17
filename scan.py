#!/usr/bin/env python3
"""
em-dex scanner — indexes the em-dash `XXX — YYY` openers in your agent
transcripts and regenerates a self-contained dashboard.

Two layers, deliberately separated:
  • NEUTRAL BASE (openers.json)  — what to index. Rarity = YOUR observed
    frequency, nothing more. No tiers, no value judgments.
  • OPINION PACKS (opinions/*.json) — tiers / pedagogy / framing, LOADED not
    baked. `--opinion evan` loads Evan's opinionated view; omit it for neutral.

Harness-agnostic (Claude Code today; point --roots at any harness that logs
assistant text as JSONL — iter_assistant_lines() is the only harness-specific bit).

Usage:
    python3 scan.py --out ~/rich-renders/em-dex.html               # neutral
    python3 scan.py --opinion evan --out ~/rich-renders/em-dex-evan.html
    python3 scan.py --roots ~/.claude/projects --exclude '*sessid*'

No third-party deps. Just stdlib.
"""
import argparse, fnmatch, glob, html, json, os, re
from pathlib import Path

HERE = Path(__file__).parent
DEF_ROOTS = ["~/.claude/projects", "~/.claude-b/projects"]
LEAD = re.compile(r'^[\s>#*_\-]*(?:\d+[.)]\s*)?')

def load_base(path):
    data = json.loads(Path(path).read_text())
    for o in data["openers"]:
        pat = o.get("match") or re.escape(o["phrase"])
        o["_re"] = re.compile(r'(?:%s)\b' % pat, re.IGNORECASE)
    return data["openers"]

def resolve_opinion(name):
    if not name:
        return None
    p = Path(name)
    if not p.exists():
        p = HERE / "opinions" / (name if name.endswith(".json") else f"{name}.json")
    return json.loads(p.read_text())

def iter_assistant_lines(path):
    """Yield each line of assistant-authored text from a JSONL. HARNESS-SPECIFIC."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                raw = raw.strip()
                if not raw or '"assistant"' not in raw:
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    continue
                if obj.get("type") != "assistant":
                    continue
                content = (obj.get("message") or {}).get("content")
                if isinstance(content, list):
                    for b in content:
                        if isinstance(b, dict) and b.get("type") == "text":
                            yield from (b.get("text") or "").splitlines()
                elif isinstance(content, str):
                    yield from content.splitlines()
    except (OSError, IOError):
        return

def scan(openers, roots, excludes):
    counts = {o["phrase"]: 0 for o in openers}
    files = blocks = 0
    for root in roots:
        for path in glob.glob(os.path.join(os.path.expanduser(root), "**", "*.jsonl"), recursive=True):
            if any(fnmatch.fnmatch(path, ex) for ex in excludes):
                continue
            files += 1
            for line in iter_assistant_lines(path):
                blocks += 1
                s = LEAD.sub("", line)
                if not s:
                    continue
                for o in openers:
                    if o["_re"].match(s):
                        counts[o["phrase"]] += 1
    return counts, files, blocks

# ── rendering ────────────────────────────────────────────────────────────────
CSS = """
html,body{height:100%;margin:0;overflow:hidden}
#scroller{position:absolute;inset:0;overflow:auto;-webkit-overflow-scrolling:touch;padding:26px 16px 92px}
body{background:#0d1117;color:#e6edf3;font:14.5px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}
h1{font-size:1.5em;margin:.1em 0;color:#f0f6fc;letter-spacing:.5px}
h2{font-size:1.02em;margin:1.5em 0 .5em;padding-bottom:.3em;border-bottom:1px solid #21262d}
.sub{color:#8b949e;margin:.2em 0 1em}.small{color:#8b949e;font-size:.84em}a{color:#79c0ff}
code{background:#21262d;border-radius:4px;padding:1px 5px;font-size:.9em}
.bar{background:#161b22;border:1px solid #30363d;border-radius:20px;height:22px;overflow:hidden;margin:.4em 0}
.bar>i{display:block;height:100%;background:linear-gradient(90deg,#56d364,#7ee787)}
.hero{background:#161b22;border:1px solid #30363d;border-left:4px solid #56d364;border-radius:10px;padding:14px 18px;margin:.7em 0}
.note{background:#11161d;border:1px solid #30363d;border-left:4px solid #e3b341;border-radius:10px;padding:10px 16px;margin:.7em 0;color:#adbac7;font-size:.9em}
.big{font-size:1.25em;font-weight:700}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:11px;margin:.6em 0}
.mon{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:11px 12px;border-left:4px solid #6e7681}
.mon .em{font-size:2em;line-height:1}.mon .nm{font-weight:700;color:#f0f6fc;margin:.15em 0}
.mon .hint{color:#adbac7;font-size:.83em;margin-top:.35em}.mon .cnt{font-size:.74em;color:#8b949e;margin-top:.3em}
.mon .tag{position:absolute;top:9px;right:10px;font-size:.66em;font-weight:700;letter-spacing:.5px;text-transform:uppercase}
.mon{position:relative;overflow:hidden}.mon.glow{box-shadow:0 0 14px rgba(227,179,65,.16)}
.uncaught{opacity:.55;border-style:dashed}.uncaught .em{filter:brightness(0) invert(.3)}.uncaught .nm{color:#6e7681}
.fb{background:#0d1117;border:1px solid #21262d;border-radius:6px;height:6px;overflow:hidden;margin-top:.4em}.fb>i{display:block;height:100%;background:#3d5a80}
details{background:#11161d;border:1px solid #30363d;border-radius:8px;padding:8px 14px;margin:.9em 0}
summary{cursor:pointer;color:#79c0ff;font-weight:600}
ul{margin:.3em 0;padding-left:1.2em}li{margin:.3em 0}b.yy{color:#e3b341}
"""
DPAD = """
<div id="scrollnav"><button onclick="scn(0,-1)">▲</button><button onclick="scn(-1,0)">◀</button>
<button onclick="scn(1,0)">▶</button><button onclick="scn(0,1)">▼</button></div>
<style>#scrollnav{position:fixed;right:12px;bottom:12px;display:grid;grid-template-columns:repeat(3,46px);grid-template-rows:repeat(3,46px);gap:5px;z-index:99999}
#scrollnav button:nth-child(1){grid-area:1/2}#scrollnav button:nth-child(2){grid-area:2/1}#scrollnav button:nth-child(3){grid-area:2/3}#scrollnav button:nth-child(4){grid-area:3/2}
#scrollnav button{width:46px;height:46px;border-radius:50%;border:1px solid #2f3b4d;background:rgba(28,35,48,.94);color:#e6edf3;font:18px/1 system-ui;cursor:pointer}
@media(min-width:900px){#scrollnav{opacity:.55}}</style>
<script>function scn(dx,dy){var s=document.getElementById('scroller');try{s.scrollBy({left:s.clientWidth*.8*dx,top:s.clientHeight*.82*dy,behavior:'smooth'});}catch(e){}}</script>
"""
def esc(s): return html.escape(str(s))

def _page(title, body):
    return (f"<!DOCTYPE html><html lang=en><head><meta charset=utf-8>"
            f"<meta name=viewport content='width=device-width, initial-scale=1'>"
            f"<title>{esc(title)}</title><style>{CSS}</style></head>"
            f"<body><div id=scroller>{body}</div>{DPAD}</body></html>")

def render_neutral(openers, counts, meta):
    caught = sorted((o for o in openers if counts[o["phrase"]] > 0), key=lambda o: -counts[o["phrase"]])
    never = [o for o in openers if counts[o["phrase"]] == 0]
    mx = max((counts[o["phrase"]] for o in caught), default=1)
    total = sum(counts.values()) or 1
    n = len(caught)
    def descr(i):  # tertile position among caught, descriptive only
        if n <= 2: return "seen"
        t = i / n
        return "among your most frequent" if t < 1/3 else ("occasional" if t < 2/3 else "seldom (rare)")
    def card(o, i):
        c = counts[o["phrase"]]
        share = round(c / total * 100, 1)
        rel = round(c / mx * 100)
        return (f'<div class="mon"><div class="em">{o["emoji"]}</div>'
                f'<div class="nm">{esc(o["phrase"])}</div>'
                f'<div class="cnt">{c}× · {share}% of your openers · {descr(i)}</div>'
                f'<div class="fb"><i style="width:{rel}%"></i></div></div>')
    cards = "\n".join(card(o, i) for i, o in enumerate(caught))
    nevers = "".join(f'<div class="mon uncaught"><div class="em">{o["emoji"]}</div>'
                     f'<div class="nm">{esc(o["phrase"])}</div><div class="cnt">never emitted</div></div>'
                     for o in never)
    body = (f'<h1>— em-dex</h1>'
            f'<p class="sub">the em-dash opener dex · <b>neutral view</b> · every <code>XXX — YYY</code> opener you emit, ranked by how often · harness-agnostic</p>'
            f'<div class="hero"><span class="big">Trainer: {esc(meta["trainer"])} — {n}/{len(openers)} distinct openers seen</span>'
            f'<span class="small"><br>{meta["files"]} transcripts · {meta["blocks"]:,} assistant blocks</span></div>'
            f'<div class="note"><b>Rarity here means one thing: seldom emitted.</b> Nothing is prized or graded — '
            f'a rare opener like <code>Both done</code> is rare because the <i>situation</i> is rare, not because it\'s better. '
            f'Want tiers, hints, a skill-tree framing? Those are opinions — load a pack: <code>scan.py --opinion evan</code>.</div>'
            f'<h2>▮ By frequency (most → least)</h2><div class="grid">{cards}</div>')
    if nevers:
        body += f'<h2>▯ Never emitted</h2><div class="grid">{nevers}</div>'
    return _page(f"em-dex (neutral) — {meta['trainer']}", body)

def render_opinion(openers, counts, op, meta):
    tiers = {t["id"]: t for t in op["tiers"]}
    ann = op["annotations"]
    unit = op.get("unit_plural", "openers")
    total = len(openers)
    caught = sum(1 for o in openers if counts[o["phrase"]] > 0)
    pct = round(caught / total * 100) if total else 0
    def card(o):
        p = o["phrase"]; c = counts[p]; a = ann.get(p, {})
        tid = a.get("tier", "situational"); t = tiers.get(tid, {"color": "#6e7681"})
        glow = " glow" if t.get("glow") else ""
        cls = "mon" + glow + ("" if c else " uncaught")
        if c:
            cnt = (f"caught ×{c} — earned or flattered? unknowable" if tid == "shiny" else f"caught ×{c}")
            wild = ""
        else:
            cnt = "not yet caught — 0"
            wild = ' <span class="tag" style="color:#e3b341">✦ wild</span>' if tid in ("legendary", "shiny") else ""
        return (f'<div class="{cls}" style="border-left-color:{t["color"]}">{wild}'
                f'<div class="em">{o["emoji"]}</div><div class="nm">{esc(p)}</div>'
                f'<div class="hint">{esc(a.get("hint",""))}</div><div class="cnt">{cnt}</div></div>')
    secs = []
    for t in op["tiers"]:
        members = [o for o in openers if ann.get(o["phrase"], {}).get("tier") == t["id"]]
        if not members:
            continue
        secs.append(f'<h2>{t["emoji"]} {esc(t["label"])}</h2><div class="grid">{"".join(card(o) for o in members)}</div>')
    body = (f'<h1>— {esc(op["title"])}</h1>'
            f'<p class="sub">the em-dash opener dex · <b>opinion pack loaded</b> · harness-agnostic</p>'
            f'<div class="hero"><span class="big">Trainer: {esc(meta["trainer"])} — {caught}/{total} {esc(unit)} caught ({pct}%)</span>'
            f'<div class="bar"><i style="width:{pct}%"></i></div>'
            f'<span class="small">{meta["files"]} transcripts · {meta["blocks"]:,} assistant blocks</span></div>'
            f'<div class="note">{esc(op["intro"])}</div>' + "".join(secs))
    return _page(f"{op['title']} — {meta['trainer']}", body)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(HERE / "openers.json"))
    ap.add_argument("--opinion", default=None, help="opinion pack name (e.g. 'evan') or path; omit for neutral")
    ap.add_argument("--roots", nargs="+", default=DEF_ROOTS)
    ap.add_argument("--exclude", nargs="*", default=[])
    ap.add_argument("--trainer", default=os.environ.get("USER", "you"))
    ap.add_argument("--out", default=str(HERE / "em-dex.html"))
    a = ap.parse_args()

    openers = load_base(a.base)
    op = resolve_opinion(a.opinion)
    counts, files, blocks = scan(openers, a.roots, [os.path.expanduser(x) for x in a.exclude])
    meta = {"trainer": a.trainer, "files": files, "blocks": blocks}
    out = os.path.expanduser(a.out)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(render_opinion(openers, counts, op, meta) if op else render_neutral(openers, counts, meta))

    mode = f"opinion:{op['title']}" if op else "neutral"
    seen = sum(1 for o in openers if counts[o["phrase"]] > 0)
    print(f"[{mode}] scanned {files} files, {blocks:,} blocks · {seen}/{len(openers)} openers seen")
    for o in openers:
        c = counts[o["phrase"]]
        print(f"  {'✓' if c else '·'} {o['phrase']:<26} {c}")
    print(f"\nwrote {out}")

if __name__ == "__main__":
    main()

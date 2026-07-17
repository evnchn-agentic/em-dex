#!/usr/bin/env python3
"""
em-dex compare — a high-dimensional PROFILE diff of two cohorts' opener use.

NOT a score. NOT a ranking. A core design principle: you can't project "how good
with agents" onto one axis (PCA — the explained variance is low), and any level
becomes a Goodhart target the instant it's aimed at. So compare shows the WHOLE
distribution and *where two profiles diverge* — never who is "higher".

Cohorts today = model strings (the transcripts we have). Person-vs-person drops
into the exact same shape once other people's transcripts attach — and it stays
safe by construction, because there is no scalar to rank anyone by.

    python3 compare.py --a opus-4-8 --b sonnet-5 --out ~/rich-renders/em-dex-compare.html
"""
import argparse, fnmatch, glob, json, os
from pathlib import Path
import scan as dex

def iter_model_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                if '"assistant"' not in raw:
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    continue
                if obj.get("type") != "assistant":
                    continue
                msg = obj.get("message") or {}
                model = msg.get("model") or ""
                content = msg.get("content")
                if isinstance(content, list):
                    for b in content:
                        if isinstance(b, dict) and b.get("type") == "text":
                            for line in (b.get("text") or "").splitlines():
                                yield model, line
                elif isinstance(content, str):
                    for line in content.splitlines():
                        yield model, line
    except (OSError, IOError):
        return

def scan_two(openers, roots, excludes, apat, bpat):
    ca = {o["phrase"]: 0 for o in openers}
    cb = {o["phrase"]: 0 for o in openers}
    seen = {"a": 0, "b": 0, "ambiguous": 0}
    for root in roots:
        for path in glob.glob(os.path.join(os.path.expanduser(root), "**", "*.jsonl"), recursive=True):
            if any(fnmatch.fnmatch(path, ex) for ex in excludes):
                continue
            for model, line in iter_model_lines(path):
                ina, inb = apat in model, bpat in model
                if ina and inb:            # overlapping cohort patterns — don't silently pick A
                    seen["ambiguous"] += 1
                    continue
                side = "a" if ina else ("b" if inb else None)
                if side is None:
                    continue
                s = dex.LEAD.sub("", line)
                if not s:
                    continue
                for o in openers:
                    if o["_re"].match(s):
                        (ca if side == "a" else cb)[o["phrase"]] += 1
                        seen[side] += 1
    return ca, cb, seen

def render(openers, ca, cb, seen, la, lb):
    ta = sum(ca.values()) or 1
    tb = sum(cb.values()) or 1
    rows = []
    for o in openers:
        ra = ca[o["phrase"]] / ta * 100
        rb = cb[o["phrase"]] / tb * 100
        rows.append((o, ra, rb, ra - rb))
    rows.sort(key=lambda r: -abs(r[3]))
    mx = max((max(r[1], r[2]) for r in rows), default=1) or 1
    def row(o, ra, rb, d):
        aw = round(ra / mx * 100); bw = round(rb / mx * 100)
        lean = la if d > 0 else lb
        ask = f'<span class="ask">→ what makes {esc(lean)} lean here?</span>' if abs(d) >= 1.0 else ""
        return (
            f'<tr><td class="op">{o["emoji"]} {esc(o["phrase"])}</td>'
            f'<td class="ra">{ra:.1f}%</td>'
            f'<td class="dv"><div class="db">'
            f'<div class="half l"><span style="width:{aw}%;background:#79c0ff"></span></div>'
            f'<div class="half r"><span style="width:{bw}%;background:#e3b341"></span></div>'
            f'</div></td>'
            f'<td class="rb">{rb:.1f}%</td>'
            f'<td class="d">{d:+.1f}pp {ask}</td></tr>')
    body = f"""
<style>
.cmpstyle table{{width:100%;border-collapse:collapse;font-size:.86em}}
.cmpstyle td,.cmpstyle th{{padding:5px 8px;border-bottom:1px solid #21262d;vertical-align:middle}}
.cmpstyle th{{color:#8b949e;text-align:left;font-weight:600}}
.cmpstyle td.op{{font-weight:700;color:#f0f6fc;white-space:nowrap}}
.cmpstyle td.ra{{color:#79c0ff;text-align:right;width:60px}}
.cmpstyle td.rb{{color:#e3b341;width:60px}}
.cmpstyle td.d{{color:#8b949e;font-size:.9em}}
.cmpstyle .ask{{color:#adbac7;font-style:italic}}
.db{{display:flex;align-items:center;height:12px;min-width:180px}}
.half{{width:50%;display:flex}}.half.l{{justify-content:flex-end}}
.half span{{display:block;height:8px;border-radius:2px}}
.lg span{{display:inline-block;width:11px;height:11px;border-radius:2px;vertical-align:middle;margin:0 4px}}
</style>
<h1>— em-dex · compare</h1>
<p class="sub">a <b>profile diff</b>, not a score · <span class="lg"><span style="background:#79c0ff"></span></span>{esc(la)}
 vs <span class="lg"><span style="background:#e3b341"></span></span>{esc(lb)} · ranked by divergence · harness-agnostic</p>
<div class="note"><b>There is deliberately no overall score, similarity number, or ranking.</b>
A core design principle: "how well you work with agents" doesn't project onto one axis
(PCA — low explained variance), and the moment a level becomes a target it stops measuring
anything real (Goodhart). em-dex refuses to collapse the profile to axis-1. This shows the
<i>whole distribution</i> and where the two diverge — a conversation starter ("ask why?"),
never a verdict on who is better.</div>
<div class="hero"><span class="small">{esc(la)}: {seen['a']:,} openers · {esc(lb)}: {seen['b']:,} openers ·
each row = that opener's share of the cohort's total openers (so cohort size doesn't skew it)</span></div>
<div class="cmpstyle"><table>
<tr><th>opener</th><th style="text-align:right">{esc(la)}</th><th style="text-align:center">divergence</th><th>{esc(lb)}</th><th>Δ</th></tr>
{"".join(row(*r) for r in rows)}
</table></div>
<p class="small">Cohorts are model strings here (the transcripts on hand). Person-vs-person uses the
identical view once other transcripts attach — and stays safe, because there is no scalar to rank anyone by.</p>
"""
    return dex._page(f"em-dex compare — {la} vs {lb}", body)

def esc(s): return dex.esc(s)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(dex.HERE / "openers.json"))
    ap.add_argument("--a", default="claude-opus-4-8")
    ap.add_argument("--b", default="claude-sonnet-5")
    ap.add_argument("--a-label", default=None)
    ap.add_argument("--b-label", default=None)
    ap.add_argument("--roots", nargs="+", default=dex.DEF_ROOTS)
    ap.add_argument("--exclude", nargs="*", default=[])
    ap.add_argument("--out", default=str(dex.HERE / "em-dex-compare.html"))
    a = ap.parse_args()

    openers = dex.load_base(a.base)
    ca, cb, seen = scan_two(openers, a.roots, [os.path.expanduser(x) for x in a.exclude], a.a, a.b)
    la = a.a_label or a.a
    lb = a.b_label or a.b
    out = os.path.expanduser(a.out)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(render(openers, ca, cb, seen, la, lb))
    print(f"[{la}] {seen['a']:,} openers vs [{lb}] {seen['b']:,} openers"
          + (f" · {seen['ambiguous']:,} skipped (matched both cohorts)" if seen.get("ambiguous") else ""))
    ta = sum(ca.values()) or 1; tb = sum(cb.values()) or 1
    div = sorted(openers, key=lambda o: -abs(ca[o["phrase"]]/ta - cb[o["phrase"]]/tb))
    print("top divergences:")
    for o in div[:6]:
        ra = ca[o["phrase"]]/ta*100; rb = cb[o["phrase"]]/tb*100
        print(f"  {o['phrase']:<24} {ra:5.1f}% vs {rb:5.1f}%  ({ra-rb:+.1f}pp)")
    print(f"\nwrote {out.replace(os.path.expanduser('~'), '~')}")

if __name__ == "__main__":
    main()

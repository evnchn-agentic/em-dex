#!/usr/bin/env python3
"""
em-dex — live NiceGUI app (the em-dash opener dex).

Neutral base (openers.json) + LOADABLE opinion packs (opinions/*.json).
By default it loads Evan's opinion pack — so it's explicitly "Evan's opinionated
em-dex", opinions LOADED not baked. DEX_OPINION=none → neutral (rarity = pure
observed frequency, no value judgments). DEX_OPINION=<name> → another pack.

Polls your agent transcripts; fires a real macOS notification on each new catch.
Harness-agnostic (Claude Code today; scan.iter_assistant_lines is the seam).

    python3 app.py                    # native window, Evan's opinion pack
    DEX_OPINION=none python3 app.py   # neutral view
    DEX_NATIVE=0 python3 app.py       # web app on :8099 (headless-testable)
"""
import json, os, subprocess
from pathlib import Path

import scan as dex
from nicegui import ui

HERE = Path(__file__).parent
OPENERS = dex.load_base(HERE / "openers.json")
OP_NAME = os.environ.get("DEX_OPINION", "evan")
OPINION = None if OP_NAME.lower() in ("none", "", "off") else dex.resolve_opinion(OP_NAME)
ROOTS = [os.path.expanduser(r) for r in dex.DEF_ROOTS]
EXCLUDE = [os.path.expanduser(x) for x in os.environ.get("DEX_EXCLUDE", "").split(os.pathsep) if x]
try:
    POLL = int(os.environ.get("DEX_POLL", "20"))
except ValueError:
    POLL = 20
NATIVE = os.environ.get("DEX_NATIVE", "1") == "1"
TITLE = OPINION["title"] if OPINION else "em-dex (neutral)"

state = {"counts": {o["phrase"]: 0 for o in OPENERS}, "files": 0, "blocks": 0, "primed": False}


def run_scan():
    counts, files, blocks = dex.scan(OPENERS, ROOTS, EXCLUDE)
    newly = []
    if state["primed"]:
        for o in OPENERS:
            if counts.get(o["phrase"], 0) > state["counts"].get(o["phrase"], 0):
                newly.append(o)
    state.update(counts=counts, files=files, blocks=blocks, primed=True)
    return newly


def mac_notify(title, message):
    try:
        subprocess.run(["osascript", "-e",
                        f"display notification {json.dumps(message)} with title {json.dumps(title)} sound name \"Glass\""],
                       check=False, capture_output=True, timeout=5)
    except Exception:
        pass


ui.dark_mode(True)
ui.add_css("""
.dexcard{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:11px 12px;border-left:4px solid #6e7681}
.dexcard .em{font-size:2em;line-height:1}.dexcard .nm{font-weight:700;color:#f0f6fc}
.dexcard .h{color:#adbac7;font-size:.82em}.dexcard .c{color:#8b949e;font-size:.75em;margin-top:.25em}
.dexcard.uncaught{opacity:.5;border-style:dashed}.dexcard.uncaught .em{filter:brightness(0) invert(.3)}
.fb{background:#0d1117;border:1px solid #21262d;border-radius:6px;height:6px;overflow:hidden;margin-top:.4em}.fb>i{display:block;height:100%;background:#3d5a80}
.tierhdr{color:#79c0ff;font-weight:700;border-bottom:1px solid #21262d;width:100%;padding-bottom:.2em;margin-top:.5em}
.note{background:#11161d;border:1px solid #30363d;border-left:4px solid #e3b341;border-radius:8px;padding:8px 14px;color:#adbac7;font-size:.85em}
""")


def _card(emoji, phrase, sub, cnt, color="#6e7681", caught=True, fb=None):
    cls = "dexcard" + ("" if caught else " uncaught")
    with ui.element("div").classes(cls).style(f"border-left-color:{color}"):
        ui.html(f'<div class="em">{emoji}</div>')
        ui.label(phrase).classes("nm")
        if sub:
            ui.label(sub).classes("h")
        ui.label(cnt).classes("c")
        if fb is not None:
            ui.html(f'<div class="fb"><i style="width:{fb}%"></i></div>')


@ui.refreshable
def dex_body():
    counts = state["counts"]
    total = len(OPENERS)
    caught = sum(1 for o in OPENERS if counts.get(o["phrase"], 0) > 0)
    with ui.column().classes("w-full max-w-4xl mx-auto gap-1"):
        ui.label(f"— {TITLE}").classes("text-2xl font-bold").style("color:#f0f6fc")
        mode = "opinion pack loaded" if OPINION else "neutral view · rarity = observed frequency, no value judgments"
        ui.label(f"the em-dash opener dex · {mode} · harness-agnostic").style("color:#8b949e;margin-top:-4px")
        _u = f"{OPINION.get('unit_plural','openers')} caught" if OPINION else "openers seen"
        ui.label(f"{caught}/{total} {_u} · {state['files']} transcripts · "
                 f"{state['blocks']:,} blocks · polling {POLL}s").style("color:#8b949e")
        ui.linear_progress(caught / total if total else 0, show_value=False).props("color=green").classes("w-full")

        if OPINION:
            ui.html(f'<div class="note">{dex.esc(OPINION["intro"])}</div>')
            ann = OPINION["annotations"]
            for t in OPINION["tiers"]:
                members = [o for o in OPENERS if ann.get(o["phrase"], {}).get("tier") == t["id"]]
                if not members:
                    continue
                ui.label(f'{t["emoji"]} {t["label"]}').classes("tierhdr")
                with ui.grid().classes("w-full gap-2").style("grid-template-columns:repeat(auto-fill,minmax(220px,1fr))"):
                    for o in members:
                        c = counts.get(o["phrase"], 0)
                        a = ann.get(o["phrase"], {})
                        if c:
                            cnt = "caught ×%d — earned or flattered? unknowable" % c if t["id"] == "shiny" else f"caught ×{c}"
                        else:
                            cnt = "✦ in the wild — not yet caught"
                        _card(o["emoji"], o["phrase"], a.get("hint", ""), cnt, t["color"], c > 0)
        else:
            ui.html('<div class="note"><b>Rarity here means one thing: seldom emitted.</b> Nothing is prized or graded — '
                    'a rare opener like <b>Both done</b> is rare because the situation is rare, not because it is better. '
                    'Want tiers &amp; a skill-tree framing? Restart with <b>DEX_OPINION=evan</b>.</div>')
            caughts = sorted((o for o in OPENERS if counts.get(o["phrase"], 0) > 0), key=lambda o: -counts[o["phrase"]])
            nevers = [o for o in OPENERS if counts.get(o["phrase"], 0) == 0]
            mx = max((counts[o["phrase"]] for o in caughts), default=1)
            tot = sum(counts.values()) or 1
            ui.label("▮ By frequency (most → least)").classes("tierhdr")
            with ui.grid().classes("w-full gap-2").style("grid-template-columns:repeat(auto-fill,minmax(220px,1fr))"):
                for o in caughts:
                    c = counts[o["phrase"]]
                    _card(o["emoji"], o["phrase"], None,
                          f"{c}× · {round(c/tot*100,1)}% of your openers", fb=round(c/mx*100))
            if nevers:
                ui.label("▯ Never emitted").classes("tierhdr")
                with ui.grid().classes("w-full gap-2").style("grid-template-columns:repeat(auto-fill,minmax(220px,1fr))"):
                    for o in nevers:
                        _card(o["emoji"], o["phrase"], None, "never emitted", caught=False)


def tick():
    for o in run_scan():
        ui.notify(f'Caught {o["phrase"]}! {o["emoji"]}', type="positive", position="top")
        mac_notify("— em-dex — new catch!", f'{o["emoji"]} {o["phrase"]}')
    dex_body.refresh()


with ui.row().classes("w-full max-w-4xl mx-auto justify-end"):
    ui.button("Rescan now", icon="refresh", on_click=tick).props("flat color=blue")
dex_body()
ui.timer(0.3, tick, once=True)
ui.timer(POLL, tick)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(native=NATIVE, reload=False, port=int(os.environ.get("DEX_PORT", "8099")),
           title=TITLE, dark=True, window_size=(1000, 820) if NATIVE else None)

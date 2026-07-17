# — em-dex

The **em-dash opener dex**. Agents love the em-dash — `XXX — YYY` — so the thing
we index *is* that opening chunk.

## Two layers, deliberately separated (this is the point)

- **Neutral base — `openers.json`.** Just *what to index*. Rarity = **your observed
  frequency, nothing more.** No tiers, no "power-user move," no value judgments. A
  rare opener like `Both done` is rare because finishing two things at once is rare —
  not something to cherish or grind. The base has *no opinions*.
- **Opinion packs — `opinions/*.json`, LOADED not baked.** Tiers, "how to catch"
  hints, the skill-tree framing, the shiny — all opinion. `opinions/evan.json` is
  *Evan's opinionated em-dex*. Load it explicitly, swap it, or run without any.

> Opinionation is fine — but it announces itself and loads from a file. It is never
> the default truth of the tool. (If you disagree with Evan's tiers, that's a feature:
> write `opinions/<you>.json`.)

## Surfaces (same backend)

| Surface | Command | View |
|---|---|---|
| **Neutral static** | `python3 scan.py --out ~/rich-renders/em-dex.html` | frequency only, no opinions |
| **Opinionated static** | `python3 scan.py --opinion evan --out ~/rich-renders/em-dex-evan.html` | Evan's tiers/hints |
| **Live app (opinion)** | `python app.py` | native window, loads `opinions/evan.json`, notifies on catch |
| **Live app (neutral)** | `DEX_OPINION=none python app.py` | frequency only |

## Setup (uv)
```bash
uv venv --python 3.12 .venv && source .venv/bin/activate && uv pip install -r requirements.txt
```

## Extending
- **Track a new opener:** add one entry to `openers.json` (`phrase`, optional `emoji`, optional `match` regex).
- **Add an opinion:** a new `opinions/<name>.json` with `title`, `intro`, `tiers[]`, and `annotations{phrase → {tier, hint}}`. Load with `--opinion <name>` / `DEX_OPINION=<name>`.
- **Another harness:** point `--roots` at its transcript dir; if its JSONL shape differs, generalize `scan.iter_assistant_lines()` — the only harness-specific function.

## Env knobs (app.py)
`DEX_OPINION=evan|none|<name>` · `DEX_NATIVE=0` web · `DEX_POLL=30` · `DEX_PORT=8099` · `DEX_EXCLUDE='*sessid*'`.

## Honesty
Counts are line-start greps of assistant text (mid-sentence mentions don't count).
In the neutral base, rarity is descriptive (seldom-emitted), never prescriptive.
`You're absolutely right` is Evan's "shiny" — ambiguous by design (earned vs
sycophancy is unknowable from the text alone).

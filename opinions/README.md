# Opinion packs — the social object

An opinion pack is **one person's lens** on the openers: how they tier them, what
they'd nudge you toward, what they'd flag. Packs are how em-dex does community —
you learn by loading someone else's lens and seeing what *they* prize, then arguing.

- **`evan.json`** — Evan's opinionated em-dex (the default; game framing, "dashlings").
- **`_template.json`** — copy this to `<yourname>.json` and make it yours.

Load one: `scan.py --opinion evan` · `DEX_OPINION=teammate python app.py`.

## Design constraints (non-negotiable)
- **No scalar. No level. No ranking of people.** You can't project "how good with
  agents" onto one axis (PCA — low explained variance), and any level becomes a
  Goodhart target the moment it's aimed at. A pack expresses *taste*, never a grade.
- **Rarity ≠ virtue.** A rare opener is rare because the situation is rare (see
  `Both done`), not because it's better. Don't build tiers that reward grinding.
- **Opinions announce themselves.** Everything a pack adds is opinion, loaded from
  a file — never the default truth of the tool. Disagree? Write your own.

## Authoring
A pack is `{ title, unit, unit_plural, intro, tiers[], annotations{} }`. `annotations`
maps a base `openers.json` phrase → `{ tier, hint }`. Unmapped openers fall into the
last tier. See `_template.json` for the shape and `evan.json` for a full example.

> A teammate's pack (`<name>.json`) is authored **by them**, not guessed by an agent.
> This repo ships only the template + the maintainer's own pack.

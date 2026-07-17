# Community baseline — privacy model (design spec, not yet built)

The optional community baseline lets em-dex say *"your `Wait` rate is 1.5%, the
community median is 0.4%"* — corpus-relative rarity, plus a sense of belonging.
It is the only feature that sends anything off your machine, so it is designed
**privacy-first and opt-in**, and specced here *before* any code exists.

## Hard constraints (non-negotiable)

1. **Opt-in only.** Nothing leaves your machine unless you run the share command.
   Default em-dex is 100% local.
2. **Aggregate frequencies only — never raw text.** The payload is a map of
   `opener → count` plus a single `total_openers`. No transcript text, no message
   snippets, no timestamps, no session ids, no file paths, no model strings tied
   to content. If it isn't a count of a phrase already in `openers.json`, it does
   not go.
3. **Show the exact payload before it sends.** The share command prints the literal
   JSON to be uploaded and requires a confirm. Approval is of *bytes*, not vibes.
4. **No identity required.** Contribution is pseudonymous/aggregate; the baseline is
   a pooled distribution, not a directory of people.
5. **No scalar. No ranking. No leaderboard.** The baseline returns *distributional
   context* (per-opener community median/spread), never a score or a rank of
   contributors. This is the same anti-1D / anti-Goodhart rule as `compare`:
   "how well you work with agents" doesn't project onto one axis, and any number
   that becomes a target stops measuring anything.
6. **Withdrawable.** A contributor can remove their contribution; the pool is
   recomputed without it.

## Example payload (the entire thing that would ever leave)

```json
{
  "schema": "em-dex-baseline/1",
  "openers": { "Done": 816, "Confirmed": 855, "Wait": 54, "Hold on": 27, ... },
  "total_openers": 3542
}
```

That is the whole contract. No text, no metadata, no identity.

## What you get back

Per opener: the community's **median share** and inter-quartile spread, so em-dex can
render *"you: 1.5% · community: 0.4% (p25–p75: 0.1–0.9%)"*. Distributional context,
never a verdict.

## Status

Spec only. Not implemented. Build gated on there being real contributors — a baseline
of one is just your own numbers with extra steps.

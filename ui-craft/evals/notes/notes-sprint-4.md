# Sprint 4 — the cost line (v4), measured on iteration-3

## Where the v2 tokens went

`evals/transcript_profile.py` prints, per assistant turn, the tools called, the
tokens billed for the turn and the size of every tool result. Run on the v2
transcripts it shows the same leaks in every run:

| leak | eval-1 | eval-2 | eval-3 | eval-4 (v3) |
|---|---|---|---|---|
| reading all four references up front | 27k chars | 26k chars | 27k chars | 20k chars |
| grepping / reading `render.mjs` to learn what it measures | 19k chars, 2 turns | 3k | 4k | 4k |
| dumping `report.json`, writing ad-hoc summarisers | 2.6k | 6.2k | 4 attempts | 5k + 1.9k |
| hand-written contrast calculators (output tokens) | — | — | 11.5k out | 16k out |
| screenshots read | 10 (5 ad-hoc clips) | 1 | 5 | 4 |
| final report (output tokens) | 5.4k | 6.4k | 8.1k | 5.7k |
| cache re-write after the rate-limit interruption | 78k | 57k | 82k | 0 |

The interruption re-cache is the environment's cost, not the skill's, and it hit
every iteration-1/2 with-skill run but not every baseline. `timing.json` now carries
`resume_cache_write_tokens` and `total_tokens_excl_resume`; the summary table shows
both. On that basis eval-2 v2 was 105k vs 68k no-skill (+53%), not +139%.

## A correction to the iteration-2 cost claim

With the re-cache split out, iteration-2 reads differently:

| token mean, 4 evals | ui-craft | ui-ux-pro-max | no skill |
|---|---|---|---|
| billed | 227k | 257k | 187k |
| net of outage re-cache | 179k | 171k | 147k |

pro-max's runs were interrupted more heavily (142k / 81k / 120k of re-cache on
evals 1–3), so "ui-craft is 12% cheaper than pro-max" was an artifact of the
outages. Net of them, ui-craft costs about 4% more than pro-max and 21% more than
no skill, for 48/49 vs 45/49 vs 40/49. That is the honest baseline v4 has to beat.

## What v4 changes (SKILL.md, render.mjs, contrast.py)

- Seven cost rules at the top of SKILL.md: scripts are black boxes; never dump
  `report.json`; no home-made probes; one contact sheet + at most one full-page
  image per round; no environment audits; match tasks read nothing beyond
  `inspect.py` and the sibling source; twenty-line reports.
- `render.mjs` ends with a `Verified` block in the report's own format — paste, don't
  recompute. Step 5 of the workflow is now "paste the block + three lines".
- `contrast.py` (stdlib): pairs, or a CSS token file with light and dark side by
  side. Step 2 says to run it on the palette roles before building.
- The references are routed: anti-generic for greenfield, one patterns section,
  constraints only for rules the loop can't measure, rubric sections 1/2/9 on the
  contact sheet.

Instruments are otherwise unchanged from v3, so iteration-3 measures two things at
once: whether the hover WARN (v2's one miss) gets fixed, and what the cost rules
save.

## Results — iteration-3 (ui-craft v4 on evals 1–3; baselines as before)

Token numbers are *comparable*: billed, minus the cache re-write after an
interruption, plus the harness-prefix cache write (~30k) when a sibling run had
already paid it. (`timing.json` keeps billed, net-of-resume and comparable.)

| | ui-craft v4 | ui-craft v2 | ui-ux-pro-max | no skill |
|---|---|---|---|---|
| eval-1 greenfield | **13/13** · 229k · 3 rounds | 12/13 · 230k | 10/13 · 222k | 8/13 · 171k |
| eval-2 established | 13/13 · 152k · 2 rounds | 13/13 · 134k | 13/13 · 147k | 13/13 · 97k |
| eval-3 de-template | 12/12 · 202k · before + 2 rounds | 12/12 · 251k | 12/12 · 235k | 9/12 · 222k |
| **pass** | **38/38** | 37/38 | 35/38 | 30/38 |
| token mean | **194k** | 205k | 201k | 164k |
| vs no skill | +19% | +25% | +23% | — |

What changed, per the transcript profiles:

- The input side shrank as designed. Tool-result text per run: 19k / 32k / 27k
  chars (v4) against 76k / 69k / 75k (v2). No reference was read whole except
  `anti-generic.md` (4.7k) on the two greenfield-ish tasks; `render.mjs` was never
  opened; `report.json` was queried for single entries; `contrast.py` replaced the
  hand-written calculators (eval-3 v2 spent 11.5k output tokens on one).
- The output side did not: 82k / 43k / 64k output tokens (v4) against 77k / 23k /
  87k (v2). Page code is a fixed cost (a whole landing page is ~20k output), and
  the rest is reasoning length, which varies run to run more than any rule moves it.
- Net: flat on eval-1 (three rounds — round 2 was clean quantitatively, then
  typographic fixes earned a third render; the rule allows it only for a FAIL, so
  that is a leak of ~12k), +13% on eval-2 (a second round for a real FAIL the
  instrument found), −20% on eval-3.
- The hover miss from v2 is gone: eval-1 13/13. The fixture's own Switch track
  (1.34:1) is now reported as *inherited* with a one-line fix instead of ignored.
- The floor for "skill + one render loop" on a small match task looks like ~150k
  comparable vs ~100k with nothing — the price of a measured guarantee, not
  something more rules will remove.

Position after four sprints, evals 1–3: **38/38 vs pro-max 35/38 at 3% fewer
tokens; vs no skill 30/38 at +19%.** With eval-4 (dark mode) included, 49/49
vs 45/49 vs 40/49.

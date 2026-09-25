# Sprint 7 — a persisted direction (direction.py) and a judge for taste (judge.py)

## direction.py

The six-line brief becomes `docs/design/brief.json`. `check` measures every colour
role light and dark — text and accent 4.5:1 on every surface, the accent's
foreground 4.5:1 on it, boundaries 3:1, hairlines exempt — and `--fix` nudges a
failing token's OKLCH lightness (never a surface) until its pairs pass. `write`
emits the `@theme` block plus the dark override into the CSS between markers
(replacing an existing `@theme` block when there is one, idempotent on re-runs)
and generates `DIRECTION.md`: brief, tokens, measured ratios, pages built. The
next session reads that file first (inspect.py already finds it), so the palette,
type and density are inherited rather than re-rolled. `from-css` seeds a brief from
a project that has tokens but no brief.

Self-test brief plants a 1.6:1 boundary and a 3.1:1 dark muted text; both are found
(4 failing pairs) and fixed (`#cfc4b8 → #968c81`, `#6b615b → #8e847d`). CI asserts it.

This is the answer to pro-max's `--design-system` MASTER.md: not a spec written in
prose, but tokens that were measured before they were written, in a file the loop
re-measures on the page.

## judge.py — does it *look* better?

Until now every win was a measured-compliance win. `judge.py` shows `claude -p` the
contact sheet (three viewports, one image, no text, no config names) and asks for
rubric scores 1–5, and, pairwise, which of two pages a design lead would ship —
asked twice with the images swapped so a position preference cancels out.

### Absolute scores, iteration-3 (evals 1–3) — overall / distinctive

| | ui-craft v4 | ui-ux-pro-max | no skill |
|---|---|---|---|
| eval-1 landing | **4** / 4 | 2 / 3 | 3 / 4 |
| eval-2 settings page | 3 / 3 | 3 / 3 | 3 / 3 |
| eval-3 de-template | **4** / 4 | 3 / 4 | 2 / 4 |
| mean overall | **3.67** | 2.67 | 2.67 |

### Pairwise (both orders agreed unless "split")

- ui-craft vs ui-ux-pro-max: **3–0** (eval-1, eval-2, eval-3 all ui-craft, confidence 3–4)
- ui-craft vs no skill: 2–0, 1 split (eval-2, where all three pages are near-identical forms)

Judge's own words on eval-1 (pro-max): "hierarchy 2 — the hero competes with a
stat band; spacing 2"; on eval-3 (no skill): "the 1440 render is broken (scrolled
past the hero)".

That last line was a finding about the *instrument*: the no-skill page uses
`scroll-behavior: smooth`, so render.mjs's "scroll through, then back to top"
animated and the fold screenshot landed mid-page. Fixed (an init script pins
instant scrolling during capture), the run re-rendered and re-judged — see below.

### eval-4 (dark mode)

The first pass compared the *light* contact sheets, which are byte-identical by
design (the task forbade light changes) — the judge said so and split. Re-judged on
`contact-dark.png` with `--dark`: overall 3 / 3 / 3; distinctive 3 (ui-craft) vs 2 / 2;
colour 4 vs 3 / 3. Pairwise both orders picked ui-craft at confidence 1 with the
comment "visually indistinguishable" — a tie, honestly. All three runs converged on
the same warm dark palette; the difference on this task was never visual, it was the
1.35:1 input border on the profile page that only the instrument saw.

### Caveats

- One judge, one pass per sheet; a 3 vs 4 is a hint, a 3–0 sweep with both orders
  agreeing is evidence.
- The judge sees pixels only. It cannot see hover, focus or dark mode unless shown
  the dark sheet; those remain the instruments' job.
- Cost: about $0.60–0.95 per judgment; the whole sprint's judging was ~$12.

## Results after the instrument fix — the honest table

Every eval-1 and eval-3 project except ui-craft v4's had `scroll-behavior: smooth`
(v4 had removed it *because* it interfered with the tool — which is itself a tell
that the loop teaches the model something). Re-rendered with instant scrolling and
re-judged, the picture changes:

| overall / distinctive | ui-craft v4 | ui-ux-pro-max | no skill |
|---|---|---|---|
| eval-1 landing | 4 / 4 | 3 / 3 (was 2 / 3) | 4 / 4 (was 3 / 4) |
| eval-2 settings page | 3 / 3 | 3 / 3 | 3 / 3 |
| eval-3 de-template | 4 / 4 | 4 / 4 (was 3 / 4) | 4 / 4 (was 2 / 4) |
| mean overall | 3.67 | 3.33 | 3.67 |
| eval-4 dark (dark sheet) | 3 / 3 | 3 / 2 | 3 / 2 |

Pairwise, both orders:

- ui-craft vs ui-ux-pro-max: **2–0, 1 split** (eval-1 ui-craft at confidence 4,
  eval-2 ui-craft, eval-3 split — the judge liked pro-max's "grid-paper canvas,
  stamped badge, perforated ticket" in one order and ui-craft's "mono digits,
  restrained red on cream" in the other)
- ui-craft vs no skill: **1–1, 1 split** (eval-1 no skill — "heavier display type
  with the peach highlight, a more deliberate identity"; eval-2 split; eval-3 ui-craft)
- eval-4 dark: tie ("visually indistinguishable")

### What this says

1. The earlier "ui-craft 3.67 vs 2.67 vs 2.67" was partly the instrument: two of the
   low scores were mid-scroll screenshots. Fixing the capture cost ui-craft its
   visual lead over no-skill. Report this, don't bury it.
2. On *taste*, ui-craft is level with a capable model working alone and slightly
   ahead of pro-max. On *measured quality* the gap is unchanged: 41/41 vs 38/41 vs
   33/41, plus the dark-mode input borders only the instrument saw. The skill's
   advantage is verification, not aesthetics — which is the thesis, now with a
   number on the other side of it.
3. The taste lever in the skill is the contact-sheet critique (step 4d) and
   `anti-generic.md`. Neither produced pages the judge preferred over a strong
   model's own instincts. If "looks better" is the next goal, that is where to
   work: a sharper critique pass (the judge's rubric wording, run by the model on
   its own contact sheet before delivering) is cheap to try and now measurable.
4. The judge also found an instrument bug on its first outing — a second use for
   it: run it on every new iteration and read the notes, not just the scores.

Spend on judging this sprint: about $14.

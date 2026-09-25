# Iteration 1 — analyst notes (running log)

## Instrument fixes discovered *by* the eval loop (all applied to ui-craft/scripts/render.mjs)

1. `sr-only` skip links (1×1 px) were counted as sub-24px targets → elements clipped to ≤1px are now treated as invisible.
2. `<button role="switch">` named via `<label for>` was flagged as an unnamed control → any element with `el.labels` is named (reported by the eval-2 with-skill run itself).
3. A 16px native radio inside a 44px `<label>` row was flagged as a sub-24px target → target rect is now the union of the control and its labels (WCAG 2.5.8 measures the clickable region). Found because it unfairly failed the eval-2 baseline.
4. Focus ring residue from the keyboard audit showed in screenshots → active element is blurred before capture.
5. favicon 404 + "Failed to load resource" console noise → replaced by URL-bearing `httpErrors` / `failedRequests` lists.

Each of these would have been invisible without a baseline to compare against.

## eval-2 established-match (both runs complete)

| | with_skill | without_skill |
|---|---|---|
| assertions | 11/11 | 11/11 |
| tokens (input+output+cache_creation) | 170,229 | 67,729 |
| wall clock | 745 s | 401 s |

- **Every assertion is non-discriminating for this eval.** The fixture's conventions are explicit enough (semantic tokens, `components/ui/*`, a sibling settings page to copy) that an unaided run matched them on every measurable criterion.
- The skill's extra cost came from: inspect.py, a baseline render of /settings/profile, two render→look→fix rounds, and a hand-tuned spacing adjustment (`-my-4`) to match the Profile card rhythm pixel-for-pixel.
- Open question for the human review: does the with-skill page *look* more faithful to the existing pages (spacing rhythm, hierarchy) than the baseline's? If not, this scenario suggests the skill needs a cheaper path when `inspect.py` says "established" and the page is simple — e.g. one verify round, no baseline render.
- Baseline note: it built a reusable `RadioGroup` primitive; the with-skill run used native radios in a fieldset "to avoid inventing a component". Both defensible; worth the user's opinion.

## Pending

eval-1 (greenfield) and eval-3 (generic→distinctive) runs were interrupted by a spend-limit 429 and resumed with context intact; grading and the viewer wait on them.

## eval-1 greenfield-landing — baseline complete (with_skill still running)

Baseline: **7/11**, 220,720 tokens, 932 s active.

- Aesthetically strong and *already* anti-generic without any skill: cream "paper ledger" look,
  one burnt-orange accent, tabular mono numbers, no purple gradients, no fake testimonials or
  logo wall, an honest FAQ instead. It also built three interactive demos (Stripe feed,
  invoice generator, currency chips) — beyond what was asked.
- But it never *measured*: 16 contrast failures (eyebrow labels in the accent colour on cream,
  3.7:1) at every viewport; 8 nav/footer links at 20px height; no typeface declared; SUMMARY.md
  has no numbers. It "reviewed screenshots" (its words) — looking without instruments.
- This is the exact gap ui-craft targets. Whether the skill closes it is what eval-1 with_skill
  will show; if the with-skill run also fails contrast/targets, the loop isn't working.
- Assertion `type-move` is partly environment-driven (fonts CDN blocked); a `<link>` still
  counts, so a with-skill run can pass it. Keep, but weigh lightly in the analysis.

## eval-3 generic-to-distinctive — with_skill complete (baseline still running)

With skill: **10/10**, 369,276 tokens, 1,175 s active (the most expensive run so far; 3 render rounds).

- Its self-reported numbers matched the grader's independent re-measurement exactly
  (0/73 contrast failures, 0 targets < 24px, 10/10 focus visible) — the report step is honest.
- One deliberate move, stated: the page is built around the queue-number display (SVG
  seven-segment digits), cream paper + one vermilion accent for buttons only, hairline rules
  instead of cards, zero shadows. All 9 copy anchors preserved; sections and links untouched.
- Named 5 template tells it removed. Kept a before/after pair.
- Cost is the concern: 3 rounds × 3 viewports × screenshots read as images. If the baseline
  lands close on assertions, the question becomes whether the visual result justifies ~3× tokens.

## eval-3 generic-to-distinctive — both complete

| | with_skill | without_skill |
|---|---|---|
| assertions | 10/10 | 8/10 (pre aria-hidden refinement) |
| tokens | 369,276 | 272,386 |
| active time | 1,175 s | 1,120 s |

- **Both runs converged on the same concept** — queue ticket × LED call board, cream paper,
  vermilion accent, LED amber/red, tabular mono numerals, no cards, no shadows. The model's own
  taste, given "餐厅排队叫号", lands there with or without anti-generic.md. So the skill did not
  buy a *different* idea here; the differentiation is in measurement and finish.
- Baseline misses: nav links at 20px (6 targets < 24px — the same miss as eval-1's baseline;
  this is the single most common defect across baselines) and a decorative ghost "024" at
  1.14:1 (see instrument note below).
- Cost gap is small this time (1.36×), because the baseline also did several screenshot rounds
  on its own. With Playwright available, unaided Claude *does* look; it just doesn't measure.

Instrument note: contrast now skips `aria-hidden="true"` subtrees (counted as decorativeSkipped),
per WCAG 1.4.3's pure-decoration exemption. Final grades will be recomputed with this version
for every run so all six share one instrument.

## Sprint 2 (cost control) — applied after iteration-1 grading, before iteration-2

Where the +61% went (transcript usage): with-skill runs had more turns (22–27 vs 12–22
assistant messages), more new context per turn (screenshots as images, report.json, inspect
output, reference files) and ~60% more output tokens (brief + 2–3 rounds of fixes + the
structured report). eval-2 with-skill also rendered /settings/profile as a baseline.

Changes: contact.png (one 1× image of all folds) is now the "look first" artifact; full-page
screenshots only on a question it raised; round 1 clean ⇒ deliver; two-round ceiling; never
render pages you didn't change. Target for iteration-2: with-skill within +25% of baseline
tokens with no assertion regressions.

## Three-way benchmark (ui-ux-pro-max added as a configuration)

| | ui-craft v1 | ui-ux-pro-max | no skill |
|---|---|---|---|
| eval-1 greenfield | 11/11 · 366k | 9/11 · 364k | 7/11 · 221k |
| eval-2 established | 11/11 · 170k | 11/11 · 198k | 11/11 · 68k |
| eval-3 de-template | 10/10 · 369k | 10/10 · 326k | 8/10 · 272k |
| **total** | **32/32 (100%)** | 30/32 (94%) | 26/32 (81%) |
| token mean | 301,685 | 296,248 | 186,945 |

- pro-max's two misses are both on eval-1: 5 text elements at 4.37:1 (`text-ink-3`) despite its
  SUMMARY claiming "all text contrast pairs ≥ 4.5:1" (it computed token pairs, not the DOM), and
  no measured numbers in the report.
- pro-max costs the same as ui-craft v1 (within 2%). Its spend goes to many search.py calls and
  its own ad-hoc Playwright checks; ours to render rounds and screenshot reads.
- Same eval-3 concept in all three configs. Distinctiveness is not where any skill differentiates.
- So the margin over pro-max on measurable quality is real but narrow (2 assertions), and it
  comes entirely from measuring the composited DOM. To widen it: dark mode (pro-max derives dark
  palettes but never renders them), interaction states, and cost — the same price for a
  strictly better guarantee is the current position; cheaper *and* better is the goal.

# Sprint 3 — deeper instruments (no new LLM runs yet)

Goal: widen the measurable gap over ui-ux-pro-max with assertions that only an
instrumented loop can pass reliably. Everything here was re-measured on the
existing iteration-2 outputs (9 runs) at zero LLM cost.

## What render.mjs v3 measures that v2 did not

| New measurement | Rule | Verdict |
|---|---|---|
| Non-text contrast of control boundaries | WCAG 1.4.11 · form fields, icon-only buttons, switches ≥ 3:1 (border or opaque fill, best of the two) | FAIL |
| Weak surface on a text-labelled button | same numbers; WCAG-exempt because the text identifies the button | WARN |
| Focus-ring contrast | outline / first box-shadow colour vs what the ring is drawn over, ≥ 3:1 | FAIL |
| Hover feedback | buttons + standalone links: at least one of 10 computed properties changes on hover (element + first 6 descendants); `aria-current` links exempt | WARN |
| `cursor: pointer` on hover | — | WARN |
| Dark mode | when a `prefers-color-scheme: dark` rule or `.dark` class styles exist: re-render with the media emulated (and the class added), re-run text contrast, non-text contrast and focus; `contact-dark.png` | FAIL (dark contrast / dark non-text / dark focus) |
| Page colours | background / text colour per rendering; used to prove the light theme survived a dark-mode addition | — |

Verified on a synthetic page with five planted defects (faint input border 1.41:1,
faint focus ring 1.24:1, button without hover, muted text that only fails in dark
3.4:1, a blue that only fails in dark 2.7:1): all five reported, the clean control
stays clean.

## Two instrument mistakes caught on the way

1. **Focus ring measured mid-transition.** Tailwind's `transition-colors` includes
   `outline-color`, so right after Tab the ring is still fading in from
   `currentColor` (white on a filled button). The first re-grade flagged 4–6 rings
   at 1.0–1.1:1 in *every* configuration on *every* primary button. Confirmed
   with a probe: immediate read = `rgb(255,253,249)`, after 400 ms = ink. Fix:
   finish every running `CSSTransition` on the focused subtree before reading.
2. **Text-labelled buttons held to a rule WCAG doesn't set.** 1.4.11 exempts a
   button whose text identifies it. Downgraded to a WARN (`weak button surface`),
   kept as FAIL for fields, icon buttons and switches, which have no text to fall
   back on.

## Fixture-inherited defects and how the grader treats them

The Maple Books fixture ships `--color-line: #e5ddd3` (1.35:1 on white) on its
`Field` border and `Switch` track, and its `Switch` had no hover state. The
established-project evals forbid touching shared tokens and primitives, so:

- non-text failures whose colour is the fixture's line token are exempt in the
  light rendering of evals 2 and 4 (`FIXTURE_LINE` in grade.py). Dark mode is the
  run's own palette and is checked in full.
- the fixture `Switch` now darkens its track on hover; the identical, untouched
  copy in every established run (md5-verified) was replaced with the fixed file
  before re-grading. This is a fixture fix applied equally to all configurations,
  not an edit of any run's output.
- the current-page nav link (`aria-current="page"`) is exempt from the hover
  probe: it is a "you are here" marker, not a target.

## Results — iteration-2 outputs re-measured with the v3 instruments

Same nine runs as `notes-iteration-2.md`; two assertions added per eval
(`hover-feedback`, `non-text-contrast`) and `focus` now also requires a 3:1 ring.

| | ui-craft v2 | ui-ux-pro-max | no skill |
|---|---|---|---|
| eval-1 greenfield | 12/13 · 279k | 10/13 · 364k | 8/13 · 221k |
| eval-2 established | 13/13 · 162k | 13/13 · 198k | 13/13 · 68k |
| eval-3 de-template | 12/12 · 282k | 12/12 · 326k | 9/12 · 272k |
| **pass** | **37/38** | 35/38 | 30/38 |
| token mean | **240,811** | 296,248 | 186,945 |

What the new measurements found:

- **hover-feedback** is the only new assertion anyone failed on these pages.
  pro-max eval-1: the logo link (×2, header + footer) and the `EUR` currency
  toggle change nothing on hover. ui-craft v2 eval-1: the logo link only — v2 had
  no hover probe, so this is exactly the miss v3 now reports as a WARN and the
  workflow tells it to fix. no-skill: same three as pro-max.
- **non-text-contrast**: clean everywhere once text-labelled buttons are held to
  the WCAG rule rather than a stricter one, and the fixture's line token is
  exempt. The v2 eval-1 page has *no* `<button>` or input at all (its buttons are
  `<a>`), so nothing was measured there — a gap worth remembering: link-buttons
  are only covered by the text-contrast and hover probes.
- **focus ring ≥ 3:1**: passes everywhere after the transition fix. Before it,
  the instrument was reporting 4–6 false failures per run.
- **dark mode**: none of the nine pages declares a dark rule, so no dark pass ran.
  This is the assertion family pro-max cannot satisfy by construction (it never
  renders), and it needs eval-4 runs to show it — three configurations, roughly
  300–400k tokens in total.

Reading: on the existing three evals the instruments widened the gap by one
assertion (eval-1: 12/13 vs 10/13) and exposed one miss in v2 that a v3 rerun
would close for free. The structural gap — dark contrast, ring contrast, hover
states measured rather than promised — only shows up on tasks that *require* those
states, which is what eval-4 is for.

## Changes to the skill in this sprint

- `scripts/render.mjs` v3: dark-mode pass (`--dark`/`--no-dark`; auto when a
  dark rule exists), non-text contrast, focus-ring contrast, hover probe,
  `pageColors`, `contact-dark.png`, `--no-hover`, `file://` targets.
- `evals/grade.py`: six new checkers (`hover-feedback`, `non-text-contrast`,
  `dark-support`, `dark-contrast`, `light-unchanged`, `summary-dark-numbers`),
  eval-4 routing, fixture-line exemption, skips runs with no outputs.
- `evals/evals.json`: new assertions on evals 1–3, `focus` text updated, eval-4
  (dark mode on Maple Books) added.
- `evals/summarize.py`: three-way table + delta patching for `benchmark.json`.
- `evals/fixtures/established` `Switch`: hover feedback on the track.
- `SKILL.md` step 4c, `references/constraints.md`, `references/critique-rubric.md`
  §8: the new measurements and how to read `contact-dark.png`.

## eval-4 — dark mode on Maple Books (new LLM runs)

Prompt: 给 Maple Books 加上深色模式：跟随系统的 prefers-color-scheme，总览页和个人资料
设置页都要支持。现有的浅色外观一点都不能变，深色下的可读性要和浅色一样好。
11 assertions; `dark-contrast`, `light-unchanged`, `summary-dark-numbers` are the
ones that need a dark rendering to prove.

| | ui-craft v3 | ui-ux-pro-max | no skill |
|---|---|---|---|
| eval-4 dark mode | **11/11** · 187k · 703 s | 10/11 · 140k · 547 s | 10/11 · 186k · 1003 s |

ui-craft v3 run notes:
- rendered a light baseline *before* editing, then proved the light theme unchanged
  by MD5 over 12 screenshots (its own idea — the skill only says "keep before and after")
- one `@media (prefers-color-scheme: dark)` block re-assigning the 14 tokens; added
  `--color-line-strong` (light value = `line`) so inputs / switch tracks / secondary
  buttons get a 3.6:1 boundary in dark while decorative hairlines stay light
- flipped the primary button to bright terracotta + dark label in dark, with the
  arithmetic in the summary (a brand light enough for 4.5:1 as text on dark cannot
  carry white text at 4.5:1)
- reported the fixture's pre-existing 1.34:1 light input border as inherited and
  left it, as the prompt forbade light changes
- round 1 clean → no second render (the cost rule from Sprint 2 held)

ui-ux-pro-max run notes:
- a strong run: token remap in one media block, `color-scheme` meta, pixel-diffed the
  light theme before/after with its own Playwright script, computed contrast for the
  pairs it thought of (body 14.2:1, muted 6.35:1, button 5.8:1 …) — none of that comes
  from the skill; the executing model did it because Playwright was on the machine.
- the miss is the one the instrument exists for: it set dark `--color-line` to #3b332e
  "so dividers keep the same visual weight as in light" (1.35:1) and used the same
  token for the input borders on the profile page. Its summary states the 1.35:1
  proudly. WCAG 1.4.11 needs 3:1 on a form-field boundary; render.mjs measured
  `input#name` / `input#email` at 1.35:1 in dark on all three viewports → fails
  `dark-contrast`. ui-craft v3 hit the same wall and added `--color-line-strong`
  (3.6:1) for control boundaries only.
- grading detail: eval-4 grades both routes now (`/` and `/settings/profile`);
  on `/` alone both configs are 11/11 because the dashboard has no inputs.

no-skill run notes:
- also a strong run: token remap, `color-scheme`, pixel-diff plus a computed-style diff
  of every element to prove the light theme unchanged, a temporary component harness
  to eyeball states in both schemes, contrast per token pair (min 6.22:1 text).
- same miss, same cause: dark `--color-line` #3b332e on panel #231e1b → the profile
  page's two input borders measure 1.35:1 in dark. It never measured a control
  boundary because it never thought of one; it measured the pairs it had named.
- the most expensive of the three (1003 s, 186k) — the self-built verification cost
  as much as the skill's instrument, and covered less.

### Reading eval-4

All three runs converged on the same design (warm dark palette, primary button
flipped to bright fill + dark label, one media block over the tokens). The
difference is not taste or effort — both baselines verified *more* elaborately than
the skill run did. The difference is *what gets measured*: the instrument walks
every control on the rendered page under the dark media query, so the input border
that both baselines tuned by eye (and described in their summaries as intentional)
is a number in the report, and the workflow says "fix every FAIL". That is the
structural gap: a skill without a renderer can only check the pairs the model
remembers to name.

Cost: v3 spent the same as no-skill and 34% more than pro-max on this task, and
was the only one to pass. pro-max was cheapest because it did the least
verification of the three.

## Iteration-2 totals with eval-4 (49 assertions)

| | ui-craft v2/v3 | ui-ux-pro-max | no skill |
|---|---|---|---|
| pass | **48/49** | 45/49 | 40/49 |
| token mean (4 evals) | 227,458 | 257,168 | 186,816 |
| vs no skill | +22% | +38% | — |
| vs pro-max | −12% | — | −27% |

(eval-1..3 with_skill rows are v2; eval-4 is v3. v3 differs from v2 only in the
instrument and the wording of step 4c, so re-running 1..3 would mostly close the
one logo-hover miss.)

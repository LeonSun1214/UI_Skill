# Sprint 6 — facts (verify.py) and the description

## verify.py — what it checks and what it found

Checks: imported packages installed · icon names exported by the installed package
(.d.ts/esm exports; closest real name suggested) · Google Fonts families and weights
exist (bundled catalog, 1,908 families, Jan 2026) and carry the subset the page's
language needs · @font-face files exist · font-family stacks whose first face nothing
loads (WARN).

Test fixture `evals/fixtures/facts-test` plants 5 failures (`Bogus` from lucide,
`FakeIcon` from heroicons, a missing package, `Frauncez`, a missing woff2); all five
are reported, with `Bus` / `CakeIcon` / `Fraunces` suggested. CI asserts the count.

Run over all 18 past eval outputs: **0 invented packages, 0 wrong icon names, 0
missing fonts** in any configuration. The models never reached for an icon package
(none was installed in the fixtures until now) and used real Google Fonts. So the
`facts` assertion is a guard, not a differentiator on the existing runs: every run
gains one passed assertion (iteration-3: 41/41 vs 38/41 vs 33/41).

The warnings are real, though: every Chinese-language page in the benchmark loads
Fraunces / IBM Plex Sans, neither of which has a chinese-simplified subset — the
headings' CJK glyphs render in the system fallback. Nobody had noticed because the
sandbox blocks Google Fonts anyway. A future assertion could require the display
face to cover the page's script.

## Description tuning

Eval set: `evals/trigger-eval.json` — 10 should-trigger (landing page, settings page
in an established app, de-templating, dark mode, an accessibility complaint, a
mobile-overflow bug, polishing a Modal, tokens + login page for a new product, an
empty state, a pre-PR look at a pricing page; Chinese and English, casual and
formal) and 10 near-miss negatives (an Express API for the same product, a Tailwind
v4 build error, Playwright e2e tests, a chart from a CSV, a pptx deck, a logo, a
re-render performance refactor, a design-token *pipeline* with no UI, i18n
extraction, landing-page copy only).

First loop (skill-creator's `run_loop.py` as shipped, 3 iterations × 2 runs):
precision 100%, recall 8–25%. Diagnosis by hand-running one positive query with
`--include-partial-messages`: the model's first tool call was `ls`/`cat` on the
project, and `run_eval.py` returns "not triggered" the moment the first tool call
is anything but `Skill`/`Read`. The skill *was* called — fifth tool use, 21 s in,
against ui-ux-pro-max, ui-styling and design in the same skills list. So the
measured recall was the detector's, not the description's. That loop cost about
$50 of `claude -p` calls for nothing usable.

Second loop: a local copy of `run_eval.py` counts a Skill/Read call naming the
command within the first 6 tool uses; the test project holds the greenfield fixture
so "look at the project first" finds something; 1 run per query, 2 iterations.
Still recall 0–17% — yet the same positive query run alone through the patched
detector triggers in 9 s. Second cause: the loop runs 5 queries in parallel and
every worker drops its own `ui-craft-skill-<id>.md` into the *same* `.claude/commands`,
so each `claude -p` sees five near-identical skills and picks one; a run only counts
when the model picked *its* copy — recall ≈ 1/5. Both defects are in the shipped
tooling, not in the description. Third loop: one worker.

Third loop (one worker, 1 run per query): the **current** description scores train
12/12 and held-out 7/8 (precision 100%, recall 75%); the optimizer stopped after the
baseline because there was nothing on the train split to learn from. The one
held-out miss was the dark-mode task ("给 Maple Books 加深色模式…") — the description
never said "dark mode", and a competing installed skill (ui-styling) does.

Fix by hand rather than by another $20 loop: add "dark mode / theme" to the
measurements and to the trigger list, plus "does anything look off before I open
the PR" (the review-only phrasing). Candidate on the missed query: 3/3 triggers.
Full-set check of the candidate, one pass: 18/20 (all 10 negatives correct; the
settings-page and dark-mode positives did not trigger *that* pass). Re-running those
two three times each: settings page 3/3, dark mode 2/3. So single-pass recall moves
by ±1–2 queries from run to run — the model sometimes starts working without
consulting any skill — and old (19/20) vs candidate (18/20) is inside that noise.
The candidate is adopted because it is a superset of the old text, keeps precision
at 100% on the near-miss negatives, and closes the one *systematic* miss.

Spend: roughly $50 on the first (broken) loop, ~$20 on the second, ~$15 on the
third plus the targeted checks. Lesson for next time: run one query by hand with
`--include-partial-messages` before paying for a loop.

Final description (0.6.0):

> Build, change, and review UI in React + Tailwind projects (Vite, Next.js) with a
> render → look → measure → fix loop … (contrast, tap targets, overflow, keyboard
> focus, hover, motion, dark mode) … a page, screen, component, layout, landing page,
> dashboard, form, settings screen, modal, empty state, dark mode or theme, or any
> visual change — including "make it look better", "polish this", "it looks too
> generic / AI-made", "match our existing style", "add dark mode", "is this
> accessible", "check the mobile view", "does anything look off before I open the
> PR" — even when they never say "design" or "UI".

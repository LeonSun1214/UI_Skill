# Changelog

## 0.9.0 — the reading list

- `inspect.py` opens with **Start here**: the classes the CSS defines with their
  declarations, by use (the vocabulary — the CSS file need not be read); the
  local modules imported by most files (the chrome, the store, the strings); one
  line per page with its signals (form, fields, list, table, dialog), the classes
  and components it uses; the route table (react-router and the Next.js App
  Router); where the strings live and which dictionary is typed; and what stands
  between a fresh browser and the page — the theme script in `index.html`, a
  splash and its storage key, the early returns in `App`, the calls the store
  makes through the API module and its base path, the dev proxy's target, the
  scripts that start a backend. Two real-repository trials had put two thirds of
  their wall clock into reading files to learn exactly this. Shared components
  carry their prop names, so a primitive can be used without opening it.
- Measured on eval-2 (a two-page fixture): reads and tokens inside the spread of
  the earlier runs — the fixture is too small for finding files to cost anything.
  The number to watch is the next real-repository task (`evals/notes/notes-sprint-9.md`).
- SKILL.md: step 1 and cost rule 6 read that section and one sibling page,
  nothing else; step 4½ starts the backend the section names before mocking.

## 0.8.3 — the review path on a real page

- `render.mjs` names the page that rendered (`page: "…" · h1 …`) in its first
  lines and flags a sign-in title: a session that did not stick had measured the
  login page with full confidence (`evals/notes/trial-sunnotice-2.md`).
- SKILL.md step 4d: on an established project, the critique's `--brief` carries
  the project's own stated rules, one line each, so the critic argues with the
  composition rather than with decisions the project has already made.

## 0.8.2 — what the first real repository taught the instruments

Nine findings from a trial on a Vite + Tailwind 3 app with a FastAPI backend, a
boot-script theme and a splash (`evals/notes/trial-sunnotice.md`); the ones that
were the skill's to fix:

- `render.mjs`: the dark pass reloads the page under the dark scheme when in-place
  emulation changes nothing (a boot script that read `matchMedia` once and set
  `data-theme` never saw the emulation; the "dark" audit had measured the light
  page). CSS keyed on `[data-theme=…]` now counts as dark support, mode
  `attribute`.
- `render.mjs`: a control drawn on a gradient or image is *unverifiable*, not a
  1:1 failure against the page colour (the theme switch's selected segment). The
  Verified block counts them.
- `render.mjs`: a focus ring drawn by the browser (`outline-style: auto`, the
  two-tone default) is visible and not measured — its computed `outline-color`
  is not what is painted; every control on a dark page had read 1.06:1.
- `render.mjs`: a pressed, checked or selected control (`aria-pressed="true"`,
  `aria-checked="true"`, `aria-selected="true"`) owes no hover feedback, like
  `aria-current` and disabled ones.
- `verify.py` strips comments before scanning imports: two JSDoc sentences had
  been reported as missing packages.
- `inspect.py` on a root with no UI stack (frontend/ + backend/, an apps/ folder
  without a workspace file) lists the app packages one and two levels down.
- `doctor.mjs` compares this copy's version with the copies installed under
  `~/.claude/skills` and `./.claude/skills` and says when one is behind;
  `install.sh` prints the version it installed; SKILL.md names its version in
  its first line. The trial ran on a 0.6.0 copy that the Skill tool had loaded.
- SKILL.md step 4d: match the tokens, critique the composition — a page type the
  project does not have yet gets the critic even in an established codebase.
  Step 4½ gains rows for a splash and for a boot-script theme.
- `selftest/real-project.html`: the four patterns above, planted; four new checks
  (15 in all).

## 0.8.1 — the critique rule, measured

- Nine variance runs with the critic in the loop (three per task on tasks 1–3): a
  round after a *would not ship* verdict flipped it in three of four cases; a round
  after a *would ship* verdict with one dimension at 3 returned the same scores. The
  rule is now: a round is owed for a not-ship verdict or two dimensions at 3 or
  below; one 3 is a note for the report. `critique.mjs` prints the verdict that way.
- The critic also runs once on a review of an existing page, after the fixes: on the
  review task the judge preferred the two pages that polished the hierarchy (active
  nav state, labelled actions) over the one that only fixed the ten defects.
- `grade.py` skips a run until its `SUMMARY.md` exists; `summarize.py` prints no
  spread for identical runs.
- The sprint notes and each iteration's summary table live in `evals/notes/`.

## 0.8.0 — an independent critic, and the review path

- `critique.mjs`: after the instruments pass, a fresh `claude -p` session that has
  seen neither the code nor the conversation views the contact sheet (and the dark
  one) and returns six rubric scores, a ship/no-ship verdict and the three changes
  that would most improve the page. SKILL.md step 4d treats the three changes like
  FAILs and owes one more round when any dimension scores 3 or below (tightened in
  0.8.1); once per round, at most twice per task, never on match tasks in an
  established project.
  Self-review is anchored on what the model just decided; this is not.
- Eval 5, *review and fix*: a working admin page (`evals/fixtures/review`) with ten
  planted defects — 4.4:1 grey text, 20 px unnamed icon buttons with the focus
  outline removed, a nine-column table that overflows at 375, colour-only status
  dots, a photo without alt, an infinite pulse with no reduced-motion rule, a
  skipped heading level, `user-scalable=no`. New grader checks: zoom allowed,
  heading order, status text, found-issues (≥ 6 of 10 named in the reply).
- `render.mjs` records the page's visible text (`bodyText`) so a grader can check
  copy without a second render; instant scrolling is pinned for the fold shots
  (smooth scrolling had produced mid-page screenshots).
- `judge.py pair --only` merges per eval; `summarize.py` shows mean ± spread
  when a configuration has several runs.

## 0.7.0 — a persisted direction, and a judge for taste

- `direction.py`: the six-line brief as `docs/design/brief.json`; `check` measures
  every colour role light and dark (text and accent 4.5:1 on every surface, the
  accent's foreground 4.5:1 on it, boundaries 3:1, hairlines exempt), `--fix`
  nudges failing tokens in OKLCH lightness, `write` emits the `@theme` block plus
  the dark override between markers in the CSS and generates `DIRECTION.md` with
  the tokens, the measured ratios and the pages built so far; `from-css` seeds a
  brief from an existing project. SKILL.md uses it for whole projects and design
  systems, and the next session reads `DIRECTION.md` first.
- `evals/judge.py`: a visual judge for the benchmark — `claude -p` looks at each
  run's contact sheet and scores hierarchy, distinctiveness, typography, spacing,
  colour and overall 1–5 against the critique rubric; pairwise mode shows two
  runs in both orders and asks which a design lead would ship. `summarize.py`
  shows the scores and the pairwise verdicts.

## 0.6.0 — facts, and a tuned description

- `verify.py`: every imported package must be installed, every icon name exported by
  its package (closest real name suggested), every Google Fonts family and weight
  must exist and carry the subset the page's language needs, every `@font-face`
  file must exist; a font-family nothing loads is a WARN. Bundled catalog of 1,908
  Google Fonts families (`scripts/data/google-fonts.json`, Jan 2026 snapshot).
- `facts` assertion in every eval; SKILL.md runs `verify.py` before the first render
  and pastes its `Facts:` line into the report.
- The description was re-tuned on a 20-query trigger eval set (see
  `evals/trigger-eval.json`).

## 0.5.0 — real projects, and a product

- `render.mjs`: `--storage-state`, `--cookie`, `--header`, `--auth` (logged-in pages);
  `--init-script`, `--mock` (data without a backend); `--wait-for` (late hydration);
  `--compare DIR` (pixel diff against a previous run, `diff-*.png`). Font entries are
  one per family; next/font fallbacks no longer count as load errors. Disabled
  controls are not probed for hover.
- `harness.mjs`: render one component in isolation (Vite + React), one cell per state.
- `login-state.mjs`: capture a session in a visible browser for `--storage-state`.
- `inspect.py`: Vue, Nuxt, Svelte, SvelteKit, Angular, Solid in the stack line;
  workspace roots list their UI app packages.
- `doctor.mjs` (`npm run doctor`), `selftest.mjs` (`npm test`, 11 checks on pages
  with planted defects), `install.sh`, CI workflow, README, this file.
- Next.js App Router fixture (`evals/fixtures/nextjs`).

## 0.4.0 — cost rules

- Seven cost rules at the top of SKILL.md: scripts are black boxes, no `report.json`
  dumps, no home-made probes, an image budget, no environment audits, match tasks read
  nothing extra, twenty-line reports.
- `render.mjs` ends with a pasteable `Verified` block.
- `contrast.py`: ratios for pairs or a CSS token file, light and dark side by side.
- Token accounting: interruption re-cache and the shared harness prefix split out so
  runs compare fairly.

## 0.3.0 — deeper instruments

- Dark-mode pass (media or `.dark` class) with its own contrast, boundary and focus
  audit and `contact-dark.png`.
- Non-text contrast per WCAG 1.4.11 (fields, icon buttons, switches FAIL; text
  buttons WARN), focus-ring contrast measured after transitions finish, hover
  feedback and cursor probe, `pageColors`.
- Eval 4 (dark mode on Maple Books); every route of an eval is graded.

## 0.2.0 — cost control

- Adaptive verify rounds (clean round 1 delivers; two-round ceiling), contact sheets
  at 1×, read the contact sheet before any full-page image, no confirmation renders.

## 0.1.0 — first version

- SKILL.md workflow (classify → inspect → brief → build → verify → report),
  `render.mjs` (screenshots + DOM audits), `inspect.py`, four references, three
  fixtures and the three-way benchmark against ui-ux-pro-max and no skill.

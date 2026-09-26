# Changelog

## 0.11.6 — a shorter SKILL.md

Every task loads the whole of SKILL.md in its first turn and carries it in every turn
after. Step 4½, what to do when a page won't just render, had grown to 5.3k characters,
a fifth of the file, of which a task uses one row.

- Step 4½ is now a compact table: each situation with the flag to use (1.8k
  characters). The explanations, and what the report says in each case, moved to
  `references/real-projects.md`, one heading per situation, read only for the one
  a task hits. "When to read what" points there.
- SKILL.md: 26.3k → 23.2k characters, about 6.6k → 5.8k tokens. No rule changed,
  and every flag the old section named is still in SKILL.md or the reference. The
  critique rules in step 4d, the next-largest block, stay as they are: they were
  tuned on measured runs.
- The frontmatter version had stayed at 0.9.1 since 0.9.1: every later bump changed
  only the `Version` line, and `install.sh` and `doctor.mjs` read the frontmatter. So
  the installer kept printing 0.9.1, and the doctor could not tell that an installed
  copy was behind. Both marks say 0.11.6 now, and CI fails when the frontmatter, the
  `Version` line and the changelog's top entry disagree. The doctor's version line
  printed "/" for the installed copy; it now prints its version and path.

## 0.11.5 — a render in a third of the time

Measured before changing anything: every phase of every viewport is now timed
(`report.json` → `timings`; `--timings` prints them). On the Next.js blog a render took
27.6 s, and 11 s of it was the hover probe at 1440: up to 20 links and buttons, each
followed by a fixed 350 ms wait for transitions and 120 ms after the mouse left.

- The hover probe switches transitions off while it runs and waits two animation
  frames instead (enough for a hover state a script sets): 11 s → 3.5 s. The dark
  pass does the same when the scheme switches (120 ms instead of 350), which also
  stops a `transition-colors` body from being measured mid-fade.
- The viewports render side by side, each in its own context, as they always had
  one: the run takes as long as the slowest viewport. `--serial` for a dev server
  that cannot take three page loads at once.

| page | before | after |
|---|---|---|
| Next.js blog, `/projects` | 27.6 s | 10.3 s (15.3 s with `--serial`) |
| Vite app (Sunnote), `/` | 20.6 s | 7.6 s |
| static test page | 9.4 s | 3.8 s |

Every FAIL, warning, focus count and hover finding was identical between the old run,
the new one, a repeat, and `--serial`. Self-test: side by side and `--serial` must agree
(26 checks); the suite runs in under two minutes.

## Evals, after 0.11.4 — the judge knows what a match task is

No change to the skill. The sixth trial's judge sent every Uses page back as
"template-grade" for doing what the brief asked, because the generic rubric
rewards distinctiveness and its score prompt never sees the brief.

- `judge.py`: a match task (`"task_type": "match"` and a `"reference"` contact
  sheet in `eval_metadata.json`) is scored against the page the brief names, on
  fit, finish, hierarchy, brief and overall. Its pair asks which page the site's
  owner would merge, and counts a new visual idea against a page.
  Results go to `judge-match.json` / `judge-pairs-match.json`. `--rubric` forces
  one, `--dry-run` prints what each run would be shown. `evals.json` tags each
  eval with its task type. `summarize.py` prefers a match verdict and lists both
  rubrics' pairs.
- Validated on the sixth trial with an off-brief control: a page with the same
  content, a gradient hero and violet cards. The generic score gives it 2, the
  same as the three pages that followed the brief. The match score gives it 1
  and them 3. The match rubric also resolved the ui-craft vs no-skill split,
  which was a position split: ui-craft now wins in both orders.
  ui-ux-pro-max still wins its pairs, at the lowest confidence. The seventh
  trial's archive page scores 4, the highest of any trial page.
  `evals/notes/trial-next-6.md`, `trial-next-7.md`.
- The fixture numbers in the README (task 2 is a match task) are still generic
  scores; re-judging them needs a render of the fixture's sibling page as the
  reference.

## 0.11.4 — the seventh trial: a thin sibling

A fresh agent added an archive page whose sibling, the Blog list, is 29 lines
that hand everything to a layout (`evals/notes/trial-next-7.md`). It read six
project files before its first render, the layout among them right after the
page the reading list pointed at, and the independent grading matched its
report: 0 contrast failures, the Blog list changed only within the header.

- SKILL.md, the compare row: a dev server that writes generated files
  (contentlayer's indexes, codegen) can move the page between the baseline and
  the after render; restore the generated file before each. The agent took its
  baseline twice for this.

## 0.11.3 — where a change is

- `--compare` says where the changed pixels are: the landmarks (header, nav, main's
  children by their heading, aside, footer) that hold nine tenths of them, up to
  three — *within the header (y 20–40 px)*, *within the header and "Software"* —
  or *spread over the page*. The second trial asked for this: 17–27 % of pixels
  changed because everything below a taller row shifted, and a percentage could
  not tell that from a colour change. The audit records the landmarks in
  `structure.landmarks`; a 2× screenshot is scaled to them.

## 0.11.2 — the three-way trial on a real repository, and the ragged grid

The fifth trial's task run under ui-ux-pro-max and with no skill, graded by the
same renderer (`evals/notes/trial-next-6.md`). ui-craft's page: fewest measured
defects, fewest files read; no skill: cheapest; ui-ux-pro-max: the judge's
choice in both orders, for one reason — four sample items per group where
ui-craft's three left a card alone in the last row.

- `render.mjs` reports a `ragged grid`: a grid or wrapping flex row, three items
  up, whose last row is short — a warning naming the container, and a findings
  line (fill the sample data, or let the last item span). Self-test `grid.html`
  (25 checks).
- SKILL.md, the look step: sample data fills the rows.
- README: the real-repository paragraph under the results table.

## 0.11.1 — where the fifth trial's tokens went

The transcript profile of the fifth trial (19 turns, 207k billed: 40k for the
first turn's cache write, 60k of output of which the code and the summary are a
quarter and deliberation the rest, 147k of cache writes that include that output
read back): three of the turns were spent on things the tools could have said.

- `--compare` compares the console, http and failed-request lines with the
  baseline's, and the Verified line says "the same 1 as the baseline" or names
  the new ones. The agent had spent two turns proving a hydration error
  pre-existed.
- `inspect.py` says when `next.config` sets `trailingSlash` (a request without
  the slash is redirected; the agent chased a 308) or `basePath`.
- SKILL.md: rule 6 adds `package.json`, `tsconfig` and `next.config` to what a
  match task does not read; rule 9: don't diff by hand what `--compare` diffs.

## 0.11.0 — the states a page is in after someone does something

- `render.mjs --act STEP` (repeatable) puts the page in the state to measure
  before the screenshots and audits: `click:SEL`, `type:SEL=TEXT`, `press:KEY`,
  `hover:SEL`, `focus:SEL`, `select:SEL=VALUE`, `wait:MS|SEL`, with any Playwright
  selector. The steps run again when the dark pass reloads. A step that finds
  nothing is a warning with the step named, and the run still measures.
- A dialog open in that state gets the dialog pattern measured: focus moved into it
  on open, Tab stays inside (a trap or a native modal), it has a name, the page
  behind it is inert, it fits the viewport or scrolls, there is a close control,
  Escape closes it (pressed last, from inside). A dialog that says `aria-modal` and
  lets Tab out fails; one that never claimed to be modal gets a warning that says
  what modal would take. A modal dialog the app opened on its own is audited too;
  a non-modal one that was simply there (a cookie bar, a widget) is left alone.
  On Sunnotice's team page the due-reminder alert turned out to claim modal and let
  Tab walk to the page behind it — the first finding of this kind.
- `alerts:` line — what the live regions say and how many fields carry
  `aria-invalid`, so a form's error state is read from the report, not guessed.
- Self-test: `dialog.html` (a dialog that follows the pattern, one that does not,
  a form, a step that finds nothing) and four checks (24 in all).

## 0.10.1 — the fifth trial, a fresh agent on Next.js

A fresh agent built a `/uses` page on the Tailwind Next.js starter blog with
0.10.0 (`evals/notes/trial-next-5.md`): 17 minutes, 207k tokens against the
third trial's 381k, nine tool calls before the first render, `localhost` from the
first render, `--compare` on the untouched sibling. What it exposed:

- The dev server's own overlay (Next's "1 Issue" badge, a `<nextjs-portal>` with
  its button in a shadow root; Vite's `<vite-error-overlay>`) sat in every
  screenshot and, because Playwright's selectors pierce shadow roots, in the hover
  and focus audits ("2 without feedback", "focus obscured"). It is hidden before
  paint now, the report says so, and its errors still count under console errors.
- SKILL.md: the project's checks run after the last render, not alongside it —
  `tsc --noEmit` writes `tsconfig.tsbuildinfo`, the dev server rebuilds, and the
  render in flight measured a half-built page; a lint script with `--fix`
  reformats files the task never touched.
- Self-test: the real-project fixture carries a Next-style overlay; the hover check
  proves it is not probed (20 checks).

## 0.10.0 — the first Next.js repositories, and a third less output

Two public Next.js apps (a Tailwind 4 + `next-themes` + contentlayer blog on
Next 15; an i18n boilerplate with route groups, `[locale]`, Clerk and a proxy on
Next 16) put through `inspect.py` and `render.mjs`, without an agent. Both scripts
worked; neither said enough.

- `render.mjs` prints the findings once: a line that holds at every viewport is
  untagged, one that holds at some carries their widths (`[375]`). The same block
  printed three times over was a third of the output (54 → 33 lines on a team page).
- `inspect.py` *Start here* on Next.js: the layouts, root first, with the css,
  `next/font`, providers and chrome each wraps a page in; the middleware and the
  routes it guards; what `[locale]` defaults to and whether `/` carries it; a thin
  page names the layout or template it renders, with that file's signals; pages
  that are server components say so. Every project: what `dark:` keys on
  (`@custom-variant dark`, `darkMode:` in the config, or the OS scheme) and who
  sets it (`next-themes`: attribute, default, storage key). Dictionaries that are
  `.json` are found now.
- `render.mjs` on `next dev`: a 403 on `/_next/*` (the dev server refusing its
  scripts from `127.0.0.1` since Next 15.2 — the page is never hydrated) gets a
  line naming the cause and the fix; HMR sockets and requests cut short by the
  render's own navigations no longer count as errors; a dark pass that needed a
  reload says so; a page with no xhr/fetch says the data came with the HTML.
- A "Sign in" link in a nav no longer marks a page as a sign-in page: the title
  or h1 has to say so, or a password field has to be there.
- A link alone in an `<li>` (a nav item) is a control, not prose: it is measured
  for size and probed for hover. Prose links stay exempt.
- Self-test: a check that the findings block is printed once (20 in all). Notes in
  `evals/notes/trial-next-4.md`.

## 0.9.2 — the requests line, from the first run on a Mac

- The `requests` line names each endpoint once with a count (`200 GET /api/auth/me ×2`)
  and says how many were distinct. A dev-mode store that fetches twice (StrictMode, a
  refetch) filled the twelve slots with repeats and pushed the calls a `--mock` needs
  behind the "…": twenty requests, eight endpoints shown, four of them twice. It also
  stops recording before the dark pass, whose reload would have counted a second load.
- Self-test: `twice.html` and a check on the printed line (19 in all).

## 0.9.1 — what the third trial and the second asked for

- `render.mjs --mock` takes an inline body (`'**/api/teams=[]'`) or a bare status
  (`'**/api/auth/me=401'`) as well as a file; the output's `requests` line lists
  every xhr/fetch the page made with its status, so the second render can mock
  all of them without guessing shapes.
- `render.mjs --dismiss Escape` (a key) or `--dismiss '.cookie-bar button'` (a
  selector) gets past a splash or a cookie bar at 0 / 400 / 900 ms after load,
  instead of an init script the model has to invent.
- `--compare` reports the height change first ("+200 px taller, then 16.8 % of
  the overlap changed"): a layout shift and a colour change no longer read alike.
- SKILL.md: cost rule 8 — behaviour goes into the project's own test runner, not
  a browser script of your own; step 4½ — a page you are changing gets a render
  before and a `--compare` after; step 5 — the contact-sheet path must be one the
  user can open. All three from the third trial (`evals/notes/trial-sunnote-3.md`).
- Self-test: `splash.html` and three new checks (18 in all).

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
  On a real repository (Sunnote, `evals/notes/trial-sunnote-3.md`): 9 read
  commands before the first render against 29 in the first trial, first render at
  tool call 16 against 38, and every read a file the task had to change.
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

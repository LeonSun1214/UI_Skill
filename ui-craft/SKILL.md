---
name: ui-craft
metadata:
  version: 0.11.6
description: >-
  Build, change, and review UI in React + Tailwind projects (Vite, Next.js) with a render → look → measure → fix loop, so what ships is checked against a real screenshot and real DOM measurements (contrast, tap targets, overflow, keyboard focus, hover, motion, dark mode) instead of guessed from code. Use this whenever the user wants a page, screen, component, layout, landing page, dashboard, form, settings screen, modal, empty state, dark mode or theme, or any visual change — including "make it look better", "polish this", "it looks too generic / AI-made", "match our existing style", "add dark mode", "is this accessible", "check the mobile view", "does anything look off before I open the PR" — even when they never say "design" or "UI". Also use it to inspect an existing project's design conventions before adding to it.
---

# ui-craft

Version 0.11.6. (An older copy of this file means the installed skill is behind the
repository: re-run `install.sh`; `doctor.mjs` says when that is the case.)

UI work has a gap that code review can't close: the first draft always has two or
three things you can only see once it's rendered — a heading that doesn't win the
hierarchy, a card row that's heavier on the left, muted text that fails contrast on
the tinted background, a tap target that's 18px tall. This skill closes that gap by
making you **look at what you built and measure it** before calling it done.

It deliberately carries no database of styles or palettes. You already know what
glassmorphism is and which fonts pair. What you don't have by default are eyes,
instruments, and this project's conventions. The scripts here provide those.

Reply in the user's language. Keep script names, paths, and code as they are.

## Cost rules — read these first

The loop is cheap only when it's used the way it's built. Every one of these was a
real leak in past runs:

1. **Don't read the scripts.** `render.mjs`, `inspect.py` and `contrast.py` are black
   boxes. This file says how to call them; what they print is the interface. Never
   grep their source to learn "what they measure" — it's listed below.
2. **Don't dump `report.json`.** The per-viewport verdict lines and the `Verified`
   block at the end of `render.mjs` output *are* the report. Open `report.json` only
   to get the selector of a FAIL you're about to fix, and print that entry alone.
3. **Don't write your own probes.** Contrast math → `contrast.py`. Screenshots and
   measurements → `render.mjs`. Package, icon and font facts → `verify.py`. A palette
   to persist → `direction.py`. If the loop can't measure something, say so in the
   report instead of building a script.
4. **Images have a budget.** One contact sheet per round. At most one full-page
   screenshot per round, and only for a question you can name before opening it.
   The critique (`critique.mjs`) is one call per round, two per task.
5. **Don't audit the environment.** No checks of installed fonts, proxies, git-ignore
   state or Chromium versions. Start the server, render, read the verdict. If a web
   font failed to load, the `Verified` block says so — report that and move on.
6. **Match tasks read nothing extra.** Adding to an established project means
   `inspect.py`, the one sibling page its *Start here* section points at, build,
   one render. Not the CSS file (the vocabulary is in the report), not the store
   (its calls are in the report), not `package.json`, `tsconfig` or `next.config`
   (the stack, scripts and dev lines carry what matters). The references are for
   greenfield work and for questions the contact sheet raises.
9. **Don't diff by hand what `--compare` diffs.** A render with `--compare <baseline>`
   also compares the console, http and failed-request lines with the baseline's:
   "the same 1 as the baseline" means the error was there before you. Reading
   two reports to say the same thing costs a turn.
7. **The report is short.** Twenty lines unless the user asked for detail: what
   changed, the pasted `Verified` block, the decisions you made, what couldn't be
   verified.
8. **Behaviour goes into the project's own tests.** A value that must clamp, a
   setting that must persist: write the unit test the project already has a
   runner for (vitest, jest, pytest). A browser script of your own to check what
   the page *does* is the expensive way; the loop measures what the page *shows*.

## Setup (first time on a machine)

The scripts live in this skill's own `scripts/` folder — the base directory shown
when this skill loaded. Call them by absolute path; never assume the working
directory.

```bash
cd <skill-dir>/scripts && npm install          # installs playwright
npx playwright install chromium                # bundled browser (once), OR
export UI_CRAFT_CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

`render.mjs` finds a browser on its own: bundled Chromium, then any Playwright
cache, then the machine's Chrome or Edge, then `UI_CRAFT_CHROME`. `inspect.py` and
`contrast.py` are standard-library Python 3; nothing to install. If a render fails
to start, run `node <skill-dir>/scripts/doctor.mjs` once and tell the user what it
says — don't debug the environment by hand.

## Workflow

### 0. Classify the request

Decide which of these you're doing, because they start differently:

- **Add to an existing project** (a new page or component in a codebase that already has UI) → step 1, then 3.
- **Greenfield** (empty project, prototype, single page) → step 2, then 3.
- **Review or fix** ("polish", "looks off", "is it accessible") → step 4 on the existing page, then fix.

Never assume the stack. Check `package.json` for `next` / `vite` / `react-router`
and the Tailwind major (v4 is CSS-first with `@theme`; v3 uses `tailwind.config.*`).

### 1. Inspect the project before touching it (existing projects)

```bash
python3 <skill-dir>/scripts/inspect.py <project-root>
```

Read the whole output. Its **Start here** section is the reading list: the classes
the CSS defines with their declarations (the vocabulary — you do not need the CSS
file), the modules every page imports (the chrome, the store, the strings), one
line per page with its signals (form, list, table, which classes and components),
the routes, where the strings live and whether a dictionary is typed, and what
stands between a fresh browser and the page — what `dark:` keys on and who sets
it, the theme script, a splash, the early returns in `App`, the requests the store
makes, the dev proxy. On Next.js it also names the layouts (root first, with the
providers and chrome each wraps a page in), the middleware and the routes it
guards, what `[locale]` defaults to, and, for a thin page that hands everything
to a layout or template, the file that is the real page. Read the one page whose
signals match yours (or the file it renders) and the vocabulary lines; that is
the whole of the reading for a match task. Below it the report has the tokens the project
*declares* and the classes the code *actually uses*: dominant color families,
radius, shadow, text sizes, semantic tokens (`bg-primary`) versus raw palette
(`bg-indigo-600`), and which primitives already exist.

Then decide explicitly, in one line, **match** or **establish**:

- The project has conventions → **match them.** Reuse its `Button`, its radius, its
  hue. Ninety percent of real UI work is additive, and a second design language in
  one PR is the fastest way to get it rejected — even if yours is prettier. Read the
  sibling pages' *source* (JSX and classes), not screenshots of them, and go
  straight to step 3. No brief, no references.
- The project is nearly empty, or the user asked to redesign → **establish**, step 2.

If `inspect.py` finds a design doc (`docs/design/DIRECTION.md`, `DESIGN.md`,
`design-system/*/MASTER.md`), read it; it outranks the usage statistics. A
`DIRECTION.md` next to a `brief.json` was generated by `direction.py`: its tokens
are the palette, its measured ratios are already known, and when you finish a page
add it to `pages` in the brief and re-run `direction.py write` so the next session
sees it.

### 2. Set a direction before writing code (greenfield, or "establish")

Read `references/anti-generic.md` first. It names the defaults you'll reach for
without noticing (indigo + Inter + three feature cards with icons in circles) and
how to get off them with one deliberate move.

Then write a six-line brief *before* any component code:

```
Audience:      who, and what state they're in when they see this
Feel:          three adjectives, at least one non-obvious
Distinctive:   the ONE deliberate choice (type, color, layout, or restraint) that makes this not-generic
Palette roles: bg / surface / text / muted / ONE accent and its job
Type:          display face + body face, and why that pair
Density:       airy (marketing) · standard (product) · dense (data)
```

Put the brief in your reply.

For a single page, check the palette roles before you build, so the first render
doesn't fail on numbers you could have known:

```bash
python3 <skill-dir>/scripts/contrast.py '#6b615b' '#fbf8f3' '#ffffff' '#b5451b'      # fg bg pairs
python3 <skill-dir>/scripts/contrast.py --css src/index.css --text ink,muted,brand --on surface,panel
```

For a whole new project, a design system, or anything the user will keep building
on, make the brief executable instead of prose:

```bash
python3 <skill-dir>/scripts/direction.py init --out docs/design/brief.json    # fill in the six lines + light/dark values
python3 <skill-dir>/scripts/direction.py check docs/design/brief.json --fix   # every role measured; failing tokens nudged in OKLCH lightness
python3 <skill-dir>/scripts/direction.py write docs/design/brief.json --css src/index.css
```

`write` emits the `@theme` block (and the dark override) into the CSS between
markers and generates `docs/design/DIRECTION.md` with the brief, the tokens and
the measured ratios. That file is what the next session reads first, so decisions
persist instead of being re-rolled. On an existing project that has tokens but no
brief, `direction.py from-css src/index.css` seeds one. Roles: text and accent
need 4.5:1 on every surface, the accent's foreground 4.5:1 on it, boundaries 3:1,
hairlines are exempt.

Read the one section of `references/patterns.md` that matches the page type
(landing, dashboard, form, auth, empty state …) for its structure and the
behaviours it owes the user. Not the whole file.

### 3. Build

The rules that get UIs rejected in review, all measured by the loop: 4.5:1 text
contrast (3:1 for large text), 3:1 on control boundaries and focus rings, 24px
minimum / 44px preferred targets, visible keyboard focus, hover feedback on buttons,
no horizontal scroll at 320–375px, `prefers-reduced-motion` respected, a label on
every control, `alt` on every image; for a dialog: focus moves into it, Tab stays
inside when it is modal, it has a name, Escape closes it, it fits the phone. `references/constraints.md` has the sources and
the rules the loop *can't* measure (forms, zoom, dragging, flashing) — open only the
section your page needs.

Reuse existing primitives. Don't add a UI library the project doesn't have. Don't
invent a new token when a matching one exists. Load a display face through
`next/font` or a `<link>` with `preconnect`, not an `@import` inside CSS (it blocks
rendering).

When the code is written, before starting a server, check the facts you had to
remember rather than read:

```bash
python3 <skill-dir>/scripts/verify.py <project-root>
```

It confirms every imported package is installed, every icon name is really
exported by its package (with the closest real name when it isn't), every Google
Fonts family and weight exists and carries the subset the page's language needs,
and every `@font-face` file is there. Fix every FAIL — each one is a broken build
or a font that silently falls back. A WARN about a missing language subset means
the display face you chose won't render that script; pick one that does (Noto
Serif SC, Noto Sans SC, LXGW WenKai …) or accept the fallback and say so.

### 4. Verify — the loop

This is the part that produces quality. Don't skip it because the code looks right.

**a. Serve the page.** For a dev server, start it in the background, wait for the
port to answer, and note the exact route you changed (`/pricing`, not `/`). For a
static file, pass the path. If a server is already listening on the port, use it
and leave it running.

**b. Render and measure:**

```bash
node <skill-dir>/scripts/render.mjs http://localhost:5173/pricing --out .ui-craft/pricing-1
```

Options: `--viewports 375,768,1440` (default) · `--dark` / `--no-dark` (dark mode is
rendered automatically when the page has a `prefers-color-scheme: dark` rule or
`.dark` class styles) · `--no-hover` · `--wait <ms>` · `--act STEP` (repeatable: what a
person does before the state you want measured — `click:SEL`, `type:SEL=TEXT`,
`press:KEY`, `hover:SEL`, `focus:SEL`, `select:SEL=VALUE`, `wait:MS|SEL`; SEL is any
Playwright selector, `text=Save` and `role=button[name="Delete"]` included) ·
`--serial` (the viewports render side by side by default; one at a time for a dev
server that cannot take three page loads at once).

It writes `contact.png` (all viewports above the fold, one image), `contact-dark.png`
when dark mode was rendered, `<w>-fold.png`, `<w>-full.png`, `<w>-dark-fold.png`, and
`report.json`. It prints one verdict line per viewport, the details of every FAIL,
and ends with a `Verified` block — the measured numbers in the exact form your
report needs.

**c. Fix every FAIL** — text contrast, non-text contrast (a field's border or fill,
every focus ring, at 3:1 against its surroundings), horizontal overflow, targets
under 24px, invisible or obscured focus, controls without a name, images without
`alt`, zoom blocked, and the same contrast checks in the dark rendering. These are
non-negotiable: they're what a reviewer or an audit catches, and they're cheap now.
WARNs (targets under 44px, buttons that change nothing on hover, `cursor` not
`pointer` on a custom control, a text button whose surface is under 3:1 against its
surroundings, animations without a reduced-motion rule, skipped heading levels, font
load errors, console errors) — fix unless there's a reason not to, and say the
reason. A button with no hover feedback is almost always a miss, not a choice. A grid whose last
row is short (three cards in two columns, one alone with an empty slot beside it)
reads unfinished before anything else is judged: the report says `ragged grid`;
fill the sample data to the row, or let the last item span.

A FAIL that comes from a shared primitive or token the user told you not to touch
(a 1.3:1 hairline on the project's own `Input`) is *inherited*: leave it, and name it
in the report with the one-line fix the owner could make.

**d. Look — cheaply, then get a second opinion.** Read `contact.png` (and
`contact-dark.png` if it exists): one image, three viewports, the first impression
at every width. Go through sections 1, 2 and 9 of `references/critique-rubric.md`
on it — for a match task, just those three sections, and only if the sheet raised
a doubt. Open one full-page screenshot only for a question the contact sheet
raised, and name the question first.

Your own look is anchored on what you just decided, so on any page whose *look*
matters (greenfield, a redesign, "make it look better") ask someone who wasn't
there:

```bash
node <skill-dir>/scripts/critique.mjs .ui-craft/pricing-1/contact.png --brief "<the six lines in one>"
```

It shows the sheet to a fresh session that sees only the pixels and the brief and
returns six scores, a ship / don't-ship verdict and the three changes that would
most improve the page. Treat the three changes like FAILs: apply them, or say in
the report why not. A *would not ship* verdict, or two or more of hierarchy,
distinctive, typography, spacing and color at 3 or below, means one more round
even when the instruments are clean. One 3 under a *would ship* verdict is a note
for the report, not a round: in the runs measured, that extra round never moved a
score. Once per round, at most twice per task. Match the tokens, critique the
composition: skip it only when the page copies a sibling's layout (a second
settings page, another list) — the existing pages set that look. A page type the
project does not have yet (a cover, a landing, an empty state) gets it even in an
established codebase. On a review of an existing page ("audit this", "看不清"),
once, after the fixes: its three changes are findings — fix the ones inside the
ask, list the rest. On an established project, put the project's own stated
rules into `--brief`, one line each, taken from its README, DIRECTION.md or the
comments in its CSS ("glass is 94 % opaque by a measured contrast proof", "the
brand gradient is the primary button") — otherwise the critic spends its three
changes undoing decisions the project has already argued for, and you learn
nothing about the composition.

**e. Apply, re-render, stop.** A clean round 1 — zero FAILs, zero WARNs, a
contact-sheet pass that found nothing you'd be embarrassed to ship, and (where it
ran) a critique that would ship it with at most one dimension at 3 — is done: deliver. Otherwise fix and render once more. A third round only if round 2 still
has a FAIL. Never render "to confirm": if the last round measured clean and your
fixes since then were only the ones it asked for, that report *is* the final
report — say so and deliver. If you're still finding things after round 3, the
direction is wrong, not the details; go back to step 2.

Keep each run's folder (`.ui-craft/<page>-<n>`) so before and after are both
there. `.ui-craft/` belongs in `.gitignore`.

### 4½. When the page won't just render (real projects)

Don't work around these by hand. Each has a flag, and the loop stays the same. The
details, and what the report says in each case, are in `references/real-projects.md`:
read only the section you hit.

| Situation | Do this |
|---|---|
| Behind a login (the output's `page:` line names a sign-in page) | the user runs `scripts/login-state.mjs <login-url> --out .ui-craft/state.json`; render with `--storage-state .ui-craft/state.json`. Google or Microsoft sign-in: `--cookie name=value` copied from their browser. A token: `--header "Authorization: Bearer …"` |
| Needs data a backend provides | start the backend if a script does (`dev.sh`, `compose.yaml`); else `--mock 'PATTERN=X'` (X a file, an inline body or a bare status) for each call on the output's `requests` line; `--init-script` seeds localStorage |
| Content appears after hydration or a fetch | `--wait-for SELECTOR` |
| A splash or cookie bar covers the page | `--dismiss Escape` or `--dismiss SELECTOR` |
| The theme is set by a script at boot | nothing: the dark pass reloads |
| One component, not a page | `scripts/harness.mjs` (Vite + React) |
| Changing a page that exists, or proving one did not change | render before touching it, `--compare` after; restore generated files (contentlayer, codegen) before each render |
| A dialog, drawer, menu, dropdown, or form error | `--act 'click:text=Delete'`, `--act 'type:SEL=x' --act press:Enter`; render the closed state too |
| The project has checks (`tsc`, lint, tests) | run them after the last render; revert what a `lint --fix` reformats |
| Monorepo | inspect, serve and render the one app you change |
| Next.js | render `http://localhost:PORT`, never `127.0.0.1`; `requests: none` means the data came with the HTML: start what `dev` starts instead of mocking |

### 5. Report

Paste the `Verified` block from the last render and the `Facts:` line from
`verify.py` — don't recompute or reword their numbers — then three short lines:

```
Verified (render.mjs · .ui-craft/pricing-2):
- Contrast: 41 text elements, 0 below threshold · 9 control boundaries, 0 below 3:1
- Dark mode: rendered (media) · 41 text elements, 0 below threshold · 9 boundaries, 0 below 3:1 · 0 focus rings below 3:1 · background rgb(251, 248, 243) → rgb(23, 20, 15)
- Targets: 0 below 24px · 2 between 24–44px
- Overflow: none at 375 / 768 / 1440
- Focus: 18/18 tabbed show a visible ring, 0 rings below 3:1, 0 obscured · Hover: 7/7 buttons and links respond
- Motion: reduced-motion rule present · 3 animated elements
- Names & alt: 0 unnamed controls · 0 images without alt · 1 h1 · 0 skipped heading levels
- Fonts: 2 declared, all loaded
Facts: 9 imports across 4 packages, 0 missing · 6 icon names checked, 0 wrong · 2 web fonts checked against Google Fonts, 0 missing · page language zh-cn · 0 warnings
Not verifiable here: Fraunces didn't load (offline) — rendered with the fallback
Inherited, not changed: the project's Input border is 1.34:1 on white; set --color-line to #948980 to fix
Critique: hierarchy 4 · distinctive 4 · typography 4 · spacing 4 · color 4 — applied 2 of 3 changes; kept the 3-up testimonials (see below)
Judgment calls: testimonials are 3-up at 1440; 2-up would breathe more
```

Include the contact-sheet path so the user can look too — a path they can open:
the project's `.ui-craft/<page>-<n>/contact.png`, or the copy you saved for them,
never a temp directory.

## When to read what

| Situation | Read |
|---|---|
| Starting on any existing codebase | run `scripts/inspect.py` — nothing else for a match task |
| The page won't just render (a login, a backend, a splash, a dialog, Next.js) | that section of `references/real-projects.md` |
| Choosing a look, or the output feels generic | `references/anti-generic.md` |
| Picking token values, light or dark | run `scripts/contrast.py` |
| A project the user will keep building on (tokens to persist) | `scripts/direction.py` — brief.json → check --fix → write |
| Code written, before the first render | run `scripts/verify.py` |
| Building a landing / dashboard / form / auth / empty state from scratch | that one section of `references/patterns.md` |
| A rule the loop can't measure (forms, zoom, dragging, flashing) | that section of `references/constraints.md` |
| The contact sheet raised a doubt | sections 1, 2, 9 of `references/critique-rubric.md`; the rest only for a long greenfield page |
| The look matters (greenfield, redesign, a page type the project lacks) | run `scripts/critique.mjs` on the contact sheet before delivering |

## What this skill doesn't do

- It doesn't pick a style from a table. Decide, and say why, in the brief.
- It doesn't install packages or change the build. Tell the user what's missing.
- It doesn't rewrite a project's existing tokens or primitives unless asked — it reports what they fail.
- It doesn't run more than two verify rounds (a third only when round two still fails a measurement); if quality isn't there by then, the direction needs rethinking, not another pass.
- It doesn't render pages it isn't changing. Existing pages are read as code.

---
name: ui-craft
description: >-
  Build, change, and review UI in React + Tailwind projects with a render → look → measure → fix loop, so what ships is checked against a real screenshot and real DOM measurements (contrast, tap targets, overflow, keyboard focus, motion) instead of guessed from code. Use this whenever the user wants a page, screen, component, layout, landing page, dashboard, form, settings screen, modal, empty state, or any visual change — including "make it look better", "polish this", "it looks too generic / AI-made", "match our existing style", "is this accessible", "check the mobile view" — even when they never say "design" or "UI". Also use it to inspect an existing project's design conventions before adding to it.
---

# ui-craft

UI work has a gap that code review can't close: the first draft always has two or
three things you can only see once it's rendered — a heading that doesn't win the
hierarchy, a card row that's heavier on the left, muted text that fails contrast on
the tinted background, a tap target that's 18px tall. This skill closes that gap by
making you **look at what you built and measure it** before calling it done.

It deliberately carries no database of styles or palettes. You already know what
glassmorphism is and which fonts pair. What you don't have by default are eyes,
instruments, and this project's conventions. The scripts here provide those.

Reply in the user's language. Keep script names, paths, and code as they are.

## Setup (first time on a machine)

The scripts live in this skill's own `scripts/` folder — the base directory shown
when this skill loaded. Call them by absolute path; never assume the working
directory.

```bash
cd <skill-dir>/scripts && npm install          # installs playwright
npx playwright install chromium                # bundled browser (once), OR
export UI_CRAFT_CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

`render.mjs` tries bundled Chromium, then the machine's Chrome or Edge, then
`UI_CRAFT_CHROME`. `inspect.py` is standard-library Python 3; nothing to install.

## Workflow

### 0. Classify the request

Decide which of these you're doing, because they start differently:

- **Add to an existing project** (a new page or component in a codebase that already has UI) → start at step 1.
- **Greenfield** (empty project, prototype, single page) → start at step 2.
- **Review or fix** ("polish", "looks off", "is it accessible") → start at step 4 on the existing page, then fix.

Never assume the stack. Check `package.json` for `next` / `vite` / `react-router`
and the Tailwind major (v4 is CSS-first with `@theme`; v3 uses `tailwind.config.*`).

### 1. Inspect the project before touching it (existing projects)

```bash
python3 <skill-dir>/scripts/inspect.py <project-root>
```

Read the whole output. It reports the tokens the project *declares* and — more
useful — the classes the code *actually uses*: dominant color families, radius,
shadow, text sizes, whether it uses semantic tokens (`bg-primary`) or raw palette
(`bg-indigo-600`), and which primitives already exist (`components/ui/button.tsx`).

Then decide explicitly, in one line, **match** or **establish**:

- The project has conventions → **match them.** Reuse its `Button`, its radius, its
  hue. Ninety percent of real UI work is additive, and a second design language in
  one PR is the fastest way to get it rejected — even if yours is prettier.
- The project is nearly empty, or the user asked to redesign → **establish**, step 2.

If `inspect.py` finds a design doc (`docs/design/DIRECTION.md`, `DESIGN.md`,
`design-system/*/MASTER.md`), read it; it outranks the usage statistics.

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

Put the brief in your reply. If the user asked for a design system or a whole new
project (not just one page), also save it as `docs/design/DIRECTION.md` so the next
session inherits the decisions instead of re-rolling them.

Consult `references/patterns.md` for the page type's structure and the behaviours
it owes the user (a live dashboard needs pause and stale states; a form needs inline
errors; a landing page needs exactly one primary action).

### 3. Build

Write the code with `references/constraints.md` at hand — the measurable rules with
their sources. The ones that get UIs rejected in review: 4.5:1 text contrast, 24px
minimum / 44px preferred targets, visible keyboard focus, no horizontal scroll at
320–375px, `prefers-reduced-motion` respected, a label on every control, `alt` on
every image.

Reuse existing primitives. Don't add a UI library the project doesn't have. Don't
invent a new token when a matching one exists. Load a display face through
`next/font` or a `<link>` with `preconnect`, not an `@import` inside CSS (it blocks
rendering).

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

This writes `375-fold.png`, `375-full.png`, `768-*.png`, `1440-*.png`, and
`report.json`, and prints a one-line verdict per viewport.

**c. Fix every FAIL in `report.json`** — contrast, horizontal overflow, targets
under 24px, invisible or obscured focus, controls without a name, images without
`alt`, zoom blocked. These are non-negotiable: they're what a reviewer or an audit
catches, and they're cheap now. WARNs (targets under 44px, animations without a
reduced-motion rule, skipped heading levels, font load errors, console errors) —
fix unless there's a reason not to, and say the reason.

**d. Look.** Read `1440-fold.png` (first impression) and `375-full.png` (does it
survive the narrow column) at minimum; `1440-full.png` when the page is long. Go
through `references/critique-rubric.md` — a list of questions to ask of a
screenshot, in the order a designer's eye moves. Write down the three to five
concrete changes it produces. "Looks fine" is not an answer; the rubric exists
because the first draft never is.

**e. Apply, re-render, repeat.** Stop when a run has zero FAILs *and* the rubric
pass produces nothing you'd be embarrassed to ship. Three rounds is the ceiling —
if you're still finding things, the direction is wrong, not the details; go back
to step 2.

Keep each run's folder (`.ui-craft/<page>-<n>`) so before and after are both
there. `.ui-craft/` belongs in `.gitignore`.

### 5. Report

End with what was verified, in numbers, not adjectives:

```
Verified (run 3 · .ui-craft/pricing-3):
- Contrast: 41 text elements checked, 0 below 4.5:1
- Targets: 0 below 24px · 2 between 24–44px (inline footer links, exempt)
- Overflow: none at 375 / 768 / 1440
- Focus: 18/18 focusables show a visible ring, none obscured
- Motion: reduced-motion rule present · 3 animated elements
Not verifiable here: Fraunces didn't load (offline) — rendered with the fallback
Judgment calls left: testimonials are 3-up at 1440; 2-up would breathe more
```

Include the fold screenshot path so the user can look too.

## When to read what

| Situation | Read |
|---|---|
| Starting on any existing codebase | run `scripts/inspect.py` |
| Choosing a look, or the output feels generic | `references/anti-generic.md` |
| Building a landing / dashboard / form / auth / empty state | that section of `references/patterns.md` |
| Writing markup and styles | `references/constraints.md` |
| Every time you open a screenshot | `references/critique-rubric.md` |

## What this skill doesn't do

- It doesn't pick a style from a table. Decide, and say why, in the brief.
- It doesn't install packages or change the build. Tell the user what's missing.
- It doesn't rewrite a project's existing tokens or primitives unless asked.
- It doesn't run more than three verify rounds; if quality isn't there by then, the direction needs rethinking, not another pass.

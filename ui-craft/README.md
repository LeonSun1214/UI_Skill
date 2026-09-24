# ui-craft

A Claude Code skill for UI work in React + Tailwind projects (Vite, Next.js) that
**renders what it built and measures it** before calling it done.

Most UI skills give the model a database of styles and palettes. ui-craft gives it
the three things it actually lacks: eyes (screenshots at three viewports, light and
dark), instruments (contrast, control boundaries, focus rings, tap targets,
overflow, hover feedback, motion — measured on the live DOM), and the project's own
conventions (an inspector that reads the tokens and classes the code really uses).
The model already knows what glassmorphism is.

## What you get

| Task | Without ui-craft | With ui-craft |
|---|---|---|
| "帮我做一个落地页" | a page that *looks* right in code | the same page, rendered at 375/768/1440, every text element measured, focus tabbed through, buttons hovered — and the numbers in the reply |
| "跟现有页面风格完全一致" | the model guesses the conventions | `inspect.py` lists the tokens, radius, shadow, primitives the code uses; the new page reuses them |
| "加上深色模式" | colours chosen by eye | the dark rendering audited like the light one — the input border that reads fine on white and vanishes on dark is a number in the report |
| "看起来太像 AI 模板" | a different template | a before/after render, the template tells named, one deliberate move |
| a Chinese page set in Fraunces, an icon that lucide never had | a broken build or a silent fallback | `verify.py` names the invented package, icon or font before the first render |

Measured against [ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)
and against no skill on four tasks (greenfield landing page, page in an established
codebase, de-templating a homepage, adding dark mode), graded by a programmatic
grader that re-renders every output:

| | ui-craft | ui-ux-pro-max | no skill |
|---|---|---|---|
| assertions passed | **49 / 49** | 45 / 49 | 40 / 49 |
| tokens per task (comparable, evals 1–3) | 194k | 201k | 164k |

The misses of the other two are what a renderer catches and a database cannot: text at
4.37:1 reported as "≥ 4.5:1", buttons that change nothing on hover, dark-mode input
borders at 1.35:1 described as intentional. Details in `evals/` and the sprint notes.

## Install

```bash
git clone <this repo> && bash UI_Skill/ui-craft/install.sh          # → ~/.claude/skills/ui-craft
bash UI_Skill/ui-craft/install.sh --project                          # → ./.claude/skills/ui-craft (one project)
```

The installer copies the skill, installs Playwright, reuses a Chrome/Chromium already
on the machine (or downloads the bundled one), and runs `doctor`:

```
ok    node         v22.12.0
ok    playwright   installed in …/scripts/node_modules/playwright
ok    chromium     Google Chrome (140.0.7339.80)
ok    python3      Python 3.12.3
ok    render loop  test page rendered, 4 FAILs found (expected ≥ 3: the page plants them)
ready: the render loop works on this machine.
```

Requirements: Node 18+, Python 3 (standard library only), any Chromium-based browser.
Nothing is installed into your projects; render output goes to `.ui-craft/` (git-ignore it).

## Use

Just ask. The skill triggers on UI requests in any wording — "make it look better",
"polish this", "match our existing style", "is this accessible", "check the mobile
view". It replies in your language and ends with the measured numbers:

```
Verified (render.mjs · .ui-craft/pricing-2):
- Contrast: 41 text elements, 0 below threshold · 9 control boundaries, 0 below 3:1
- Dark mode: rendered (media) · 41 text elements, 0 below threshold · …
- Targets: 0 below 24px · 2 between 24–44px
- Overflow: none at 375 / 768 / 1440
- Focus: 18/18 tabbed show a visible ring, 0 rings below 3:1, 0 obscured · Hover: 7/7 buttons and links respond
- Motion: reduced-motion rule present · 3 animated elements
- Names & alt: 0 unnamed controls · 0 images without alt · 1 h1 · 0 skipped heading levels
- Fonts: 2 declared, all loaded
```

### Real projects

| Situation | What the skill does |
|---|---|
| Page behind a login | `node scripts/login-state.mjs <login-url>` opens a window, you log in, the session is saved; renders replay it with `--storage-state`. Or `--cookie`, `--header "Authorization: Bearer …"`, `--auth user:pass`. |
| Page needs data | `--mock '**/api/items=fixture.json'` answers requests from a file; `--init-script seed.js` runs before the app (localStorage, flags). |
| SPA that hydrates late | `--wait-for '[data-loaded]'` |
| One component, not a page | `node scripts/harness.mjs <project> --component src/ui/Button.tsx --states '[…]'` writes a Vite-served page that mounts it once per state |
| Did the light theme change? | `--compare .ui-craft/before` pixel-diffs every screenshot against a previous run and writes `diff-*.png` |
| Monorepo | `inspect.py` on the workspace root lists the app packages; run it on the one you are changing |
| Next.js | works with `next dev`; `inspect.py` reads the App Router and `next/font` |

## Scripts

All standard tools; the skill calls them, and so can you.

| Script | Purpose |
|---|---|
| `scripts/render.mjs <url\|file>` | screenshots + audits at 375/768/1440, dark pass when the page has a dark rule, `contact.png`, `report.json`, the `Verified` block |
| `scripts/inspect.py <project>` | stack, declared tokens, fonts, primitives, and the classes the code actually uses; verdict *match* or *establish* |
| `scripts/contrast.py fg bg …` / `--css tokens.css` | WCAG ratios for pairs or a token file, light and dark side by side |
| `scripts/verify.py <project>` | the facts a model invents: imported packages installed, icon names exported, Google Fonts families/weights real and carrying the page's language subset, `@font-face` files present |
| `scripts/direction.py init / check --fix / write / from-css` | the brief as `brief.json`: every colour role measured light and dark, failing tokens nudged, the `@theme` block written into the CSS and `DIRECTION.md` generated so the next session inherits the decisions |
| `scripts/harness.mjs` | component-in-isolation page for Vite + React |
| `scripts/login-state.mjs` | capture a logged-in session for `--storage-state` |
| `scripts/doctor.mjs` (`npm run doctor`) | is this machine ready? |
| `scripts/selftest.mjs` (`npm test`) | renders pages with planted defects and checks the instruments report exactly those, plus every real-project option |

`references/` holds the four documents the workflow routes to: `anti-generic.md`
(the defaults you reach for without noticing), `critique-rubric.md` (how to look at
a screenshot), `constraints.md` (the rules with sources, marked measured or manual),
`patterns.md` (what each page type owes the user).

## Evals

`evals/` is the benchmark: prompts and assertions (`evals.json`), three fixture
projects plus a Next.js one, an objective grader that re-renders every output
(`grade.py`), a visual judge that scores the contact sheets and compares
configurations pairwise (`judge.py`), token accounting from transcripts
(`timing_from_transcript.py`, `transcript_profile.py`) and a three-way summary
(`summarize.py`). Runs live in a
git-ignored `ui-craft-workspace/`; see the sprint notes there for what each
iteration changed and why.

## Limits

- Web only, React first. `render.mjs` works on any URL; `inspect.py` understands
  Tailwind (v3 config or v4 `@theme`) and reads Vue/Svelte/Astro files, but the
  workflow and fixtures are React. No React Native, Flutter or SwiftUI.
- It measures what the DOM exposes. Text over images and gradients is reported as
  unverifiable; colour-only meaning, zoom to 200%, dragging alternatives and flashing
  are listed in `constraints.md` as manual checks.
- It does not judge taste. The rubric and the anti-generic list push the model off
  its defaults; whether the result is beautiful is still yours to decide.
- It needs a browser. Setup is heavier than a text-only skill — that is the price of
  seeing the page.

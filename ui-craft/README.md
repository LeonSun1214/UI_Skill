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
and against no skill on five tasks — greenfield landing page, page in an established
codebase, de-templating a homepage, adding dark mode, review-and-fix of a page with
ten planted defects — graded by a programmatic grader that re-renders every output.
ui-craft and no-skill ran three times each on tasks 1–3 (cells are means, spread
noted); ui-ux-pro-max once per task:

| | ui-craft | ui-ux-pro-max | no skill |
|---|---|---|---|
| assertions passed, tasks 1–3 + review (56) | **56 / 56** in every run | 53 / 56 | 50.7 / 56 (±1 per task) |
| dark-mode task (12, earlier iteration) | **12 / 12** | 11 / 12 | 11 / 12 |
| tokens per task (comparable, tasks 1–3) | 212k | 201k | 176k |
| tokens, review task | **162k** | 275k | 180k |
| visual judge, overall 1–5 (tasks 1–3, generic rubric) | 3.67 | 3.33 | 3.56 |
| pairwise vs ui-craft, both orders (tasks 1–3) | — | 0–2, 1 split | 0–3 |

On a real repository (the Tailwind Next.js starter blog, one "add a Uses page
that matches Projects" task, one run per configuration, `evals/notes/trial-next-6.md`)
the three are closer: ui-craft's page has the fewest measured defects (8 text
contrast failures against 10 and 10, 7 small targets against 17 and 7) and read
11 project files before its first look against 21 and 25; no skill was cheapest
(188k tokens against 207k and 264k). Judged against the Projects page it had to
match, all three pages score overall 3 of 5 (an off-brief control scores 1);
head to head, ui-craft's page beats the unaided one in both orders, and
ui-ux-pro-max's beats ui-craft's at the judge's lowest confidence, for a fuller
grid (ui-craft's three sample items left an orphan card; a check since 0.11.2).
A second task (an archive page matching the Blog list, `evals/notes/trial-next-7.md`)
came out the same page under all three configurations: identical measurements, and a
judge that could not separate them. ui-craft read 7 project files before its first
look against 31 and 41, and used about half the tool calls and tokens (133k against
244k and 276k; the other two ran side by side, which inflates their numbers somewhat).
Fewer defects or the same ones, fewer reads, at a similar or lower cost; not a wide
margin on what a design lead sees.

The misses of the other two are what a renderer catches and a database cannot, and
they repeat run after run: body text at 3.7:1, 20 px nav links, focus rings at
1.04:1, buttons that change nothing on hover, a landing page left in the system
font, a report with no numbers in it. On looks alone the picture is narrower: the
absolute judge puts nearly every page at 4 and hands out no 5s, so on that scale
ui-craft (3.67) and a strong model working unaided (3.56) are level. Head to head,
the judge picked ui-craft's page over the unaided one on all three tasks and over
ui-ux-pro-max on two, with one split. On the review task it picked the other two,
which polished the hierarchy where ui-craft only fixed the defects — since 0.8.1
the critic runs there too. The advantage is verification; on taste the evidence is
a lean, not a margin. Details in `evals/notes/`.

## Install

```bash
git clone https://github.com/LeonSun1214/UI_Skill.git
bash UI_Skill/ui-craft/install.sh                                    # → ~/.claude/skills/ui-craft
bash UI_Skill/ui-craft/install.sh --project                          # → ./.claude/skills/ui-craft (one project)
```

The path is relative to wherever the clone landed: from your home folder the
script is `UI_Skill/ui-craft/install.sh`, not `ui-craft/install.sh`.

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

After pulling a newer version, run the installer again: the skill Claude loads is the
copy under `~/.claude/skills`, not the repository, and `doctor` warns when that copy
is older than the one it is run from.

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
| A dialog, a menu, a form's error state | `--act 'click:text=Delete'`, `--act 'type:input[name=email]=x' --act press:Enter` put the page in that state first; a dialog gets its own audit (focus inside, Tab trapped when modal, a name, Escape, fits the phone) and the live region's text is quoted |
| Page needs data | `--mock '**/api/items=fixture.json'` answers requests from a file, `'**/api/teams=[]'` inline, `'**/api/auth/me=401'` a bare status; the output lists every xhr/fetch the page made with its status. `--init-script seed.js` runs before the app (localStorage, flags). |
| A splash or cookie bar covers the page | `--dismiss Escape` or `--dismiss '.cookie-bar button'` |
| SPA that hydrates late | `--wait-for '[data-loaded]'` |
| One component, not a page | `node scripts/harness.mjs <project> --component src/ui/Button.tsx --states '[…]'` writes a Vite-served page that mounts it once per state |
| Did the light theme change? | `--compare .ui-craft/before` pixel-diffs every screenshot against a previous run and writes `diff-*.png` |
| Monorepo | `inspect.py` on the workspace root lists the app packages; run it on the one you are changing |
| Next.js | works with `next dev` (render through `localhost`, not `127.0.0.1`: newer dev servers refuse their own scripts from another host); `inspect.py` reads the App Router — layouts, middleware, `[locale]`, the file a thin page renders — and `next/font` |

## Scripts

All standard tools; the skill calls them, and so can you.

| Script | Purpose |
|---|---|
| `scripts/render.mjs <url\|file>` | screenshots + audits at 375/768/1440, dark pass when the page has a dark rule, `--act` steps for dialogs, menus and error states, `contact.png`, `report.json`, the `Verified` block |
| `scripts/inspect.py <project>` | a *Start here* reading list (the CSS vocabulary with declarations, what every page imports, one line per page, routes, where the strings live, what runs before a page renders — what `dark:` keys on and who sets it, the Next.js layouts and middleware), then stack, declared tokens, fonts, primitives and the classes the code actually uses; verdict *match* or *establish* |
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
configurations pairwise (`judge.py`; a match task is judged against a contact sheet
of the page it must match, a greenfield task on its own), token accounting from transcripts
(`timing_from_transcript.py`, `transcript_profile.py`) and a three-way summary
(`summarize.py`). `evals/notes/` holds the sprint notes — what each iteration
changed and why — and every iteration's summary table; the raw runs live in a
git-ignored `ui-craft-workspace/`.

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

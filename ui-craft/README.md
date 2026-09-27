# ui-craft

A Claude Code skill for UI work in web projects built with React, Vue, Svelte, Astro,
Angular, Laravel Blade or plain HTML (Vite, Next.js, Nuxt, SvelteKit, Angular CLI, Livewire,
Inertia, Eleventy, Jekyll; Tailwind, Bootstrap, MUI, Ant Design, Chakra, Element Plus, Vuetify,
styled-components, CSS Modules or plain CSS), in React Native / Expo apps through
react-native-web, and in Flutter apps through a widget test, that **renders what it built and
measures it** before calling it done.

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
margin on what a design lead sees. The same archive task on a Nuxt UI template
(`evals/notes/trial-nuxt-8.md`) again came out one page three times, measured the
same, and the judge could not separate them. ui-craft read 9 project files before
its first look against 35 and 29, and made 49 tool calls against 106 and 74. But
it used about as many tokens as the unaided agent (204k against 201k;
ui-ux-pro-max 287k): each of its turns carries more. One claim was checked: the
unaided agent measured that the Blog list's dates are a day early in China, while
ui-craft's agent asserted, without measuring, that they agree.

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

Requirements: Node 18+, Python 3 (standard library only), any Chromium-based browser; the
Flutter SDK for rendering a Flutter app.
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
| Page behind a login | `node scripts/login-state.mjs <login-url>` opens a window, you log in, the session is saved; renders replay it with `--storage-state`. With a test account, sign in once from the render itself: `--act` steps on the sign-in page and `--save-state state.json`, then `--storage-state state.json` on every other page (signing in on every render trips rate limits, and the output names the error page it got instead). Or `--cookie`, `--header "Authorization: Bearer …"`, `--auth user:pass`. |
| A dialog, a menu, a form's error state | `--act 'click:text=Delete'`, `--act 'type:input[name=email]=x' --act press:Enter` put the page in that state first; a dialog gets its own audit (focus inside, Tab trapped when modal, a name, Escape, fits the phone) and the live region's text is quoted |
| Page needs data | `--mock '**/api/items=fixture.json'` answers requests from a file, `'**/api/teams=[]'` inline, `'**/api/auth/me=401'` a bare status; the output lists every xhr/fetch the app made with its status (the framework's own are counted, not listed). `--init-script seed.js` runs before the app (localStorage, flags). |
| A kit from a CDN did not load | the output's `did not load` line names each stylesheet and script another host failed to serve, before any measurement is read; `--mock '**/bootstrap.min.css=./bootstrap.min.css'` answers each from a local copy (`npm pack bootstrap@5.3.3`) |
| A splash or cookie bar covers the page | `--dismiss Escape` or `--dismiss '.cookie-bar button'` |
| SPA that hydrates late | `--wait-for '[data-loaded]'` |
| One component, not a page | `node scripts/harness.mjs <project> --component src/ui/Button.tsx --states '[…]'` writes a Vite-served page that mounts it once per state (React) |
| Did the light theme change? | `--compare .ui-craft/before` pixel-diffs every screenshot against a previous run and writes `diff-*.png` |
| Monorepo | `inspect.py` on the workspace root lists the app packages; run it on the one you are changing |
| Next.js | works with `next dev` (render through `localhost`, not `127.0.0.1`: newer dev servers refuse their own scripts from another host); `inspect.py` reads the App Router — layouts, middleware, `[locale]`, the file a thin page renders — and `next/font` |
| Nuxt | works with `nuxt dev`; `inspect.py` reads the file routes, layouts and the pages each wraps, auto-imported components, route middleware, `server/api`, @nuxt/content collections, Nuxt UI's colours and components and color-mode. Nuxt DevTools is hidden during renders. Notes: `references/stacks/nuxt.md` |
| Vue + Vite | `inspect.py` reads the vue-router table (lazy imports, redirects), the wrapper component each view sits in, `defineProps`, Pinia's storage keys and the component kit (Element Plus, Vuetify, PrimeVue, Naive UI). Notes: `references/stacks/vue.md` |
| SvelteKit | `inspect.py` reads the file routes (route groups dropped), each `+layout.svelte` and the pages it wraps, what loads a page's data (`+page.ts`, `+page.server.ts`, form actions), `hooks.server.ts` and the paths it guards, `+server.ts` endpoints, props from `$props()` or `export let`, mode-watcher. Notes: `references/stacks/sveltekit.md` |
| Astro | `inspect.py` reads the file routes and endpoints, the layout each page sits in, content collections and their folders, islands (`client:*`), middleware, integrations, Starlight's docs pages, and dark mode set by an inline script over plain CSS variables. The render hides Astro's dev toolbar. Notes: `references/stacks/astro.md` |
| Angular | `inspect.py` follows the route table from `provideRouter` / `RouterModule.forRoot` through lazy components, lazy NgModules and default-export route files (tsconfig path aliases and barrels resolved), and prints one line per page with its route, template and the layout whose `<router-outlet>` holds it; each guard with the pages it covers, where it redirects and the storage key of the session it reads; each service's `HttpClient` requests, and on the page line the calls that page makes; components by selector with their inputs and outputs; the Angular Material theme (M3 or M2, palettes, `--mat-sys-*` use); the dark-theme class and the service that sets it. The render reads Material's focus where it draws it (a field's outline beside the input, a ring on an inner layer) and reports the faint state-layer tint Material shows by default. Notes: `references/stacks/angular.md` |
| Laravel | `inspect.py` reads `routes/web.php` and the files it requires (groups, prefixes, resource routes, Fortify's views), follows each GET route to what it shows (a Blade view, a controller's `return view(…)`, a Livewire page, an Inertia page) with the middleware of the route, its group and the controller, and prints one line per view with the layout chain around it (`@extends` or a layout component, Livewire's default layout included); Blade components by use with their `@props`; Flux; `@vite` and what a first run needs. Notes: `references/stacks/laravel.md` |
| Hand-written HTML | `inspect.py` lists each page with its route and title, the kit and libraries the pages load (Bootstrap, Tailwind's CDN build, Bulma, Alpine, htmx … from a CDN or `vendor/`, with versions), and the header, nav, sidebar and footer copied into every page: how many pages hold each and how many copies are identical once the current item is set aside, so a nav change is made in every copy. Notes: `references/stacks/static.md` |
| Eleventy, Jekyll | `inspect.py` reads the config (Eleventy's directories, Jekyll's `permalink` and `defaults`), each template's route, its layout chain (through directory data files and `defaults`), its includes, and the site data; Hugo is detected. Notes: `references/stacks/static.md` |
| A component kit or CSS-in-JS | `inspect.py` reads the kit's theme where the project keeps it (MUI's `createTheme` palette, radius, fonts and overrides; Ant Design's tokens in `ConfigProvider` or umi's config and ProLayout settings; Chakra's `extendTheme` scales; Element Plus's variables and a runtime theme picker; Vuetify's themes and component defaults; a styled-components theme object and the keys components read), counts the kit's components by use, says how the code styles itself (`sx`, `styled()`, CSS Modules) and how dark mode switches, with the `--dark-storage` key (`mui-mode`, `chakra-ui-color-mode`, VueUse's `vueuse-color-scheme`, the app's own). On a React app it follows the route table (objects, `<Route>` elements, umi's `config/routes.ts`) to every page with its layout and guards. The render reads MUI's focus ripple and Vuetify's focus overlay, and says when a dark pass moved nothing instead of counting its findings twice. Notes: `references/stacks/kits.md` |
| React Native / Expo | `npx expo start --web` serves the app through react-native-web, and the render works on it: a `Pressable` without a role (a focusable `<div>`) is counted as a control and reported as `no role`; a page that scrolls inside a ScrollView gets a full screenshot of all of it; the dark pass tries a dark device (react-native-web reads the scheme in JS) and is dropped when nothing moves; `--storage 'mmkv.default\KEY=…'` puts a session or an onboarding flag where MMKV or AsyncStorage keep it. `inspect.py` lists the screens (Expo Router's files and layouts with their redirects; React Navigation's navigators, the auth branch each screen sits in, the linking path), the theme's colour map with both schemes and the contrast of its text colours (React Navigation's and Paper's defaults filled in behind a spread), the spacing scale, `StyleSheet` numbers, fonts, the `.web.tsx` twins, and the storage keys with their names in a browser. Notes: `references/stacks/react-native.md` |
| Flutter | `scripts/flutter_render.mjs <project>` renders it through Flutter itself (on the web Flutter draws one canvas, which a browser audit cannot read): a widget test starts the app through its `main()` with shared_preferences and path_provider mocked and the app's fonts loaded (Roboto, Material Icons, the pubspec's fonts, google_fonts' faces fetched once), and at 375 / 768 / 1440, in light and dark and at 200 % text, saves screenshots and measures the contrast of every text and icon, tap targets against 48dp and 44pt, labels on tappable nodes, and layout overflow, each finding with the widget's file and line. `--route` arrives like a deep link, `--prefs KEY=VALUE` sets the flag a redirect reads, `--enter` and `--tap` walk through a form, `--widget` pushes one screen (`--standalone` when `main()` cannot start in a test). `inspect.py` lists the screens (go_router with shells and redirects, auto_route, named routes), the `ColorScheme` per brightness with the contrast of its pairs, the `TextTheme`'s own colours, palette and spacing classes, fonts, the shared_preferences keys, and the plugins a test has no platform for. Notes: `references/stacks/flutter.md` |
| A theme service switches dark mode | `--dark-storage theme=dark` sets the app's stored choice for the dark pass and reloads, so the app's own switch runs (a body class, a stored setting) instead of a class the render guesses; the inspector prints the flag when it finds the service |

## Scripts

All standard tools; the skill calls them, and so can you.

| Script | Purpose |
|---|---|
| `scripts/render.mjs <url\|file>` | screenshots + audits at 375/768/1440, dark pass when the page has a dark rule, `--act` steps for dialogs, menus and error states, `contact.png`, `report.json`, the `Verified` block |
| `scripts/inspect.py <project>` | a *Start here* reading list (the CSS vocabulary with declarations, what every page imports, one line per page, routes, where the strings live, what runs before a page renders — what `dark:` keys on and who sets it, the Next.js and Nuxt layouts and middleware), then stack, declared tokens, fonts, primitives and the classes the code actually uses; verdict *match* or *establish* |
| `scripts/contrast.py fg bg …` / `--css tokens.css` | WCAG ratios for pairs or a token file, light and dark side by side |
| `scripts/verify.py <project>` | the facts a model invents: imported packages installed, icon names exported, Google Fonts families/weights real and carrying the page's language subset, `@font-face` files present |
| `scripts/direction.py init / check --fix / write / from-css` | the brief as `brief.json`: every colour role measured light and dark, failing tokens nudged, the `@theme` block written into the CSS and `DIRECTION.md` generated so the next session inherits the decisions |
| `scripts/flutter_render.mjs <project>` | the render for a Flutter app: a widget test with screenshots at 375/768/1440, light and dark and 200 % text, contrast of every text and icon, tap targets, labels, overflow with file and line, `contact.png`, `report.json`, the `Verified` block |
| `scripts/harness.mjs` | component-in-isolation page for Vite + React (React only) |
| `scripts/login-state.mjs` | capture a logged-in session for `--storage-state` |
| `scripts/doctor.mjs` (`npm run doctor`) | is this machine ready? |
| `scripts/selftest.mjs` (`npm test`) | renders pages with planted defects and checks the instruments report exactly those, plus every real-project option |

`references/` holds the documents the workflow routes to: `anti-generic.md`
(the defaults you reach for without noticing), `critique-rubric.md` (how to look at
a screenshot), `constraints.md` (the rules with sources, marked measured or manual),
`patterns.md` (what each page type owes the user), `real-projects.md` (a page that
won't just render) and `stacks/` (what differs in a Nuxt, Vue, SvelteKit, Astro, Angular,
Laravel, React Native, Flutter or static-site project, and with a component kit).

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

- Web, React Native through react-native-web, and Flutter through a widget test. `render.mjs` works on any URL; `inspect.py`
  understands Tailwind (v3 config or v4 `@theme`), Bootstrap and plain CSS variables, Next.js,
  Nuxt, Vue + Vite, SvelteKit, Astro, Angular, Laravel (Blade, Livewire, Inertia), Eleventy,
  Jekyll and hand-written HTML, the themes of MUI, Ant Design, Chakra, Element Plus, Vuetify,
  styled-components, Emotion and CSS Modules, and React Native (Expo Router, React Navigation,
  theme colour maps, React Native Paper, NativeWind / Uniwind) and Flutter (go_router, auto_route,
  named routes, ThemeData and ColorScheme, Material and Cupertino). The benchmark tasks are React
  and Nuxt; the other stacks are checked on fixtures and real projects, not yet on a full task.
  A React Native app without react-native-web cannot be rendered: the inspector's contrast of
  the theme's pairs and the stack notes' checklist are what is left, and what only a phone
  shows (native tab bars, safe areas, `hitSlop`, the user's font size) is not measured. Not yet:
  Rails and Django templates, Hugo's templates, and the themes of Mantine, Naive UI, PrimeVue,
  Quasar, Ant Design Vue and Tamagui (detected, not read). The component harness is React
  only. No SwiftUI yet.
- A Flutter render is a widget test on the machine, not a phone: no network (images from the web
  show their placeholder unless `--network` reaches the host), no plugins beyond the two it mocks,
  no native libraries or Firebase (the app's error screen is reported as such; `--widget …
  --standalone` renders a screen without them), and Cupertino text is drawn in Roboto. It needs
  the Flutter SDK.
- It measures what the DOM exposes. Text over images and gradients is reported as
  unverifiable; colour-only meaning, zoom to 200%, dragging alternatives and flashing
  are listed in `constraints.md` as manual checks.
- It does not judge taste. The rubric and the anti-generic list push the model off
  its defaults; whether the result is beautiful is still yours to decide.
- It needs a browser. Setup is heavier than a text-only skill — that is the price of
  seeing the page.

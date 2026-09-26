# Real projects: when the page won't just render

Each situation has a flag, and the loop stays the same. SKILL.md step 4½ lists them with
the flag to use; this file has the details and what the report says. Read only the
section you hit.

## The page is behind a login

The render output's first lines name the page that rendered (`page: "…" · h1 …`); a sign-in title there means the session did not stick. Then: ask the user to run `node <skill-dir>/scripts/login-state.mjs <login-url> --out .ui-craft/state.json` (a window opens, they log in with the app's own form, close the window, it saves the session), then render with `--storage-state .ui-craft/state.json`. Google and Microsoft sign-in refuse a browser under automation ("this browser or app may not be secure"): for an app whose only door is that button, the user copies the session cookie from their normal browser (DevTools → Application → Cookies) and passes `--cookie name=value`. A token you were given: `--header "Authorization: Bearer …"`.

## The page needs data a backend would provide

The inspector's *Start here* section names the calls the store makes and the dev proxy's target: start that backend if a script does it (`dev.sh`, `compose.yaml`). Else `--mock`: a file (`'**/api/items=.ui-craft/items.json'`), an inline body (`'**/api/teams=[]'`, `'**/api/config={"demo_mode":false}'`) or a bare status (`'**/api/auth/me=401'`, a signed-out visitor). The render output's `requests` line lists every xhr/fetch the page made with its status, so the second render can mock all of them. `--init-script .ui-craft/seed.js` runs before the app (localStorage under the key the inspector names, feature flags).

## Content appears after hydration or a fetch

`--wait-for '[data-loaded]'` (any selector that exists only when the real content does).

## A splash, intro animation or cookie bar covers the page

`--dismiss Escape` (any key name) or `--dismiss '.cookie-bar button'` (a selector to click), pressed at 0 / 400 / 900 ms after load; plus `--wait` for the fade. The report's `focus … obscured` count says whether something is still on top.

## The theme is set by a script at boot (`data-theme`)

Nothing: the dark pass reloads the page under the dark scheme when in-place emulation changes nothing, and the report names the mode (`media`, `class`, `attribute`).

## The task is one component, not a page

`node <skill-dir>/scripts/harness.mjs <project> --component src/components/ui/Button.tsx --states '[{"children":"Save"},{"variant":"secondary","children":"Cancel"},{"disabled":true,"children":"Off"}]'` writes `.ui-craft/harness/index.html`; render that URL on the project's own dev server. Vite + React only.

## You are changing a page that exists (a card on the dashboard, a row on the settings page) — or must prove one did not change

Render it before touching anything, then render after with `--compare .ui-craft/<page>-0`: the Verified block reports the height change first, then the share of the overlap that moved and where it moved (*within the header*, *within "Software"*, or *spread over the page*, with the y range), and writes `diff-*.png`. The new content is expected to differ; anything else that moved is a regression to explain. A dev server that writes generated files (contentlayer rewrites its indexes on start and whenever a watched file changes; codegen, route manifests) can move the page for reasons that are not yours: `git checkout --` the generated file before each of the two renders, so both see the same one.

## The task is a dialog, a drawer, a menu, a dropdown, or a form's error state

Render the page in that state: `--act 'click:text=Delete'` for the dialog, `--act 'hover:nav >> text=Products'` for the menu, `--act 'type:input[name=email]=x' --act press:Enter` for the error. The report then carries a *Dialog* line (focus moved inside, Tab stays inside, Escape closes, fits 375, a close control) and FAILs when a dialog that claims to be modal lets Tab out, has no name, or opens without focus; an `alerts:` line quotes what the live region says and how many fields are marked invalid. Render the closed state too, so the page under it is measured. A dialog the app opened on its own (a due-reminder, an announcement) is audited the same way when it says `aria-modal`; say whose it is.

## The project has its own checks (`tsc`, lint, tests)

Run them after the last render, not alongside it: `tsc --noEmit` still writes `tsconfig.tsbuildinfo`, a dev server rebuilds on it, and a render in flight then measures a half-built page. A lint script that carries `--fix` reformats files you never touched: revert those so the diff stays yours.

## Monorepo

`inspect.py` on the workspace root lists the UI app packages; run it, and the dev server, in the one you are changing.

## Next.js

`next dev` is slower to answer; wait for the port, then render the route **as `http://localhost:PORT`**, not `127.0.0.1`: since 15.2 the dev server refuses its own `/_next/*` scripts from any other host (403), the page is then never hydrated, and the report says so. Pages are server components unless they say `'use client'`: the `requests` line reads *none*, the data came with the HTML, and `--mock` cannot answer it — start what the `dev` script starts (a database, a content compiler). Fonts loaded through `next/font` show as loaded in the report.

# Fourth real-repository pass — two public Next.js apps, tools only (2026-09-25)

The skill claimed Next.js from 0.5 on the strength of a two-file fixture. Three
real-repository trials had all been Vite + react-router. This pass put `inspect.py`
and `render.mjs` through two public Next.js apps without an agent, to find what
breaks before a fresh agent pays for it.

| | blog | boilerplate |
|---|---|---|
| repository | timlrx/tailwind-nextjs-starter-blog | ixartz/Next-js-Boilerplate |
| stack | Next 15.5 App Router · React 19 · Tailwind 4 (`@theme`, `@custom-variant dark`) · next-themes · contentlayer2 · pliny | Next 16.3 App Router · React 19 · Tailwind 4 · next-intl (`[locale]`, route groups) · Clerk · Drizzle + PGlite · `proxy.ts` |
| `inspect.py` | 0.15 s, 94 lines | 0.08 s, 59 lines |
| `next dev` first page | 9.7 s | 7.6 s |
| `render.mjs` home | 21 contrast failures (`primary-500` pink on white, 3.58:1), 20 targets under 24 px, overflow 380 > 375 at the footer icons, 1 dark failure | 1 contrast, 1 boundary, 14 small targets at 375, 11 links without hover (sponsor logos) |

Both scripts ran to completion on both. Neither said enough, and the render on
Next 16 measured a page that was never hydrated. What changed, in order found:

1. **Thin pages.** Every page on the blog is 10–60 lines that hand everything to a
   layout (`ListLayoutWithTags`, `PostLayout`, `Main`); the boilerplate's to a
   `BaseTemplate`. The one-line-per-page list had no signals at all, so "read the
   page whose signals match yours" pointed nowhere. A page now names the local
   component it returns, when that file has signals or is page-sized, with that
   file's signals: `renders ListLayout (layouts/ListLayoutWithTags.tsx · 170 lines · list)`.
2. **Layouts.** `app/layout.tsx` is the chrome (`Header`, `SectionContainer`,
   `Footer`), the providers (`ThemeProviders`, `SearchProvider`), the font
   (`Space_Grotesk` from `next/font`) and the stylesheet — none of it was on the
   reading list. Now: one line per layout, root first, nested ones with the
   segment they wrap (`(marketing)`, `(auth)`, `dashboard`).
3. **The theme mechanism.** `@custom-variant dark (&:where(.dark, .dark *))` at
   `css/tailwind.css:5` plus `<ThemeProvider attribute="class" defaultTheme={siteMetadata.theme} enableSystem>`
   is the whole dark-mode story, and the report said only "Dark mode: present". Now
   one line: what `dark:` keys on (Tailwind 4 variant, `darkMode:` in a v3 config,
   or the OS scheme) and who sets it, with the default read out of `siteMetadata.js`
   and the storage key. Sunnote gained the same line (`darkMode: 'class'`); Sunnotice,
   which keys on CSS variables, correctly gained nothing.
4. **Middleware.** `src/proxy.ts` runs Clerk and next-intl before every page and
   guards `/dashboard(.*)`: a render there needs a session. The line names the
   guarded matcher, not every matcher (the sign-in matcher is not a guard).
5. **`[locale]`.** Nine routes started with `/[locale]/`; nothing said what it is.
   Now: `en, fr · default en · prefix as-needed → / is the default locale (src/utils/AppConfig.ts)`.
6. **Dictionaries in `.json`.** `src/locales/en.json` was not found because the
   source walk skips `.json`; the directory walk finds it now (62 keys each).
7. **Server components.** No xhr/fetch on either app: the data came with the HTML.
   The render says so instead of printing nothing, and the page line says
   `server component`, so `--mock` is not attempted.
8. **Next ≥ 15.2 refuses its own scripts from `127.0.0.1`.** The boilerplate
   returned 403 on every `/_next/static/chunks/*.js` when rendered as
   `http://127.0.0.1:3001/` (the dev log: "Blocked cross-origin request … add it
   to allowedDevOrigins"), so the render measured server HTML with no hydration:
   4 links hover-probed instead of 20. The report now names the cause and the fix
   when it sees a 403 under `/_next/`; SKILL.md and the README say `localhost`.
9. **Dev-server noise.** HMR websocket errors, requests cut short by the render's
   own reload, and a transient 500 during a recompile filled the warn line with
   "console errors 4 · failed requests 9 · http errors 7" that were none of the
   page's. The socket errors and `ERR_ABORTED` are dropped; a dark pass that needed
   a reload says so in the Verified block without changing the mode label.
10. **A "Sign in" link is not a sign-in page.** The boilerplate's home carries
    "Sign in · Sign up" in its nav, and the page line called it a sign-in page.
    The title or h1 has to say so now, or a password field has to be present.
11. **Nav links in `<li>` are controls.** Both apps put their navigation in list
    items; the target and hover audits treated an inline link inside an `<li>` as
    prose and skipped it. Prose now means the host carries text beyond the link's
    own. The boilerplate's home went from 2 to 14 small targets at 375 and from
    4 to 20 links probed for hover — the numbers a reviewer needs.

Also from this pass, not Next-specific: the findings block is printed once with
viewport tags instead of once per viewport (54 → 33 lines on Sunnotice's team
page); and the `requests` line names each endpoint once with a count (0.9.2).

What a fresh-agent trial on one of these would measure next: whether the reading
list's `renders` line is enough for a match task on a layout-driven app, and
whether the `localhost` rule in SKILL.md is read before the first render.

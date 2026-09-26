# Nuxt

Read when `inspect.py` says the stack is Nuxt. What differs from a React project, and what to do about it.

## Where things are

- Nuxt 4 keeps the app in `app/` (pages, layouts, components, middleware, `app.vue`, `app.config.ts`); Nuxt 3 keeps the same folders at the root. `server/` is the project's own backend, `content/` is @nuxt/content's.
- Routes are files: `pages/blog/[slug].vue` is `/blog/:slug`, `pages/blog/index.vue` is `/blog`, and a `pages/blog.vue` beside the `blog/` folder wraps its children through `<NuxtPage />`. A new page is a new file; there is no route table to edit.
- `layouts/default.vue` wraps every page unless the page sets `definePageMeta({ layout: 'name' })`; `app.vue` wraps everything. The inspector lists each layout with the pages that use it.
- Components are auto-imported: no import lines. The tag is the path under `components/`: `components/dashboard/Sidebar.vue` is `<DashboardSidebar>`. A new component goes in `components/` and is used by that name.

## Nuxt UI

When the stack line says Nuxt UI, the design system is its components (`UButton`, `UPageSection`, `UPageCard`, `UForm`, …) and the colour names in `app.config.ts` (`ui.colors.primary`, `neutral`). A match task builds with the components the inspector lists and with the semantic classes and props (`color="primary"`, `variant="soft"`, `text-muted`, `bg-elevated`, `border-default`), not with raw palette classes like `bg-emerald-600`.

Its defaults fail a few measurements, on every page that uses them. On a stock template the render reported:

- white text on a solid `primary` button, 3.8:1 with blue (the 500 shade), lower with green or emerald;
- focus rings in primary at 25 % (`outline-primary/25`), about 1.35:1 on white; navigation links draw theirs on `::before`, which the render reads;
- inputs outlined by a 1px inset ring (`ring-accented`), about 1.5:1 on white: the non-text line says `ring`.

These are the kit's, not your page's. In a match task leave them and name them under *Inherited*. When the user asks for them to be fixed, fix them once, at the theme, never with classes on each page: Nuxt UI points `--ui-primary` at the 500 shade (400 in dark), so `:root { --ui-primary: var(--ui-color-primary-700); }` in the main CSS darkens every primary surface; a component's classes are overridden under `ui.<component>` in `app.config.ts` (`slots`, `variants`).

## Serving and rendering

- `npm run dev` (`nuxt dev`) listens on :3000. The first request compiles for several seconds: wait until `curl -s localhost:3000` answers before the first render. `localhost` and `127.0.0.1` both work.
- A render on the dev server takes about 15 s: after load, Vite keeps sending modules, so the page never reaches network idle and each viewport waits out the limit. That is the dev server, not a hang.
- Nuxt DevTools (on by default in dev) floats over the page; the render hides it, and it is not in the screenshots.
- Pages load their data during the server render (`useFetch`, `useAsyncData`, `queryCollection`), so the `requests` line reads *none from the app* on a first load, and counts Nuxt's own traffic (`/_nuxt/`, `_payload.json`, @nuxt/content's database) without listing it. `--mock` has nothing to answer there: the data comes from `server/api/*` and `content/`, which the dev server serves. Start it, don't mock it.
- A page behind route middleware (`middleware/auth.ts`, or a `*.global.ts` that calls `navigateTo`) redirects without a session: pass the session cookie with `--cookie` or `--storage-state`.

## Dark mode

@nuxtjs/color-mode (Nuxt UI brings it) puts `class="dark"` on `<html>` before paint, from localStorage `nuxt-color-mode` or the OS preference. The render's dark pass handles it. To render dark on purpose, `--init-script` a file that sets `localStorage.setItem('nuxt-color-mode', 'dark')`.

## Checks

`npx nuxi typecheck` (needs `vue-tsc`) and the project's lint script. `nuxi prepare` writes the `.nuxt` types the checks read; run it once after an install. Run the checks after the last render: they rebuild what the dev server watches.

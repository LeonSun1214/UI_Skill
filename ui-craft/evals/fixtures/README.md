# Eval fixtures

Three small Vite + React 19 + Tailwind 4 projects used by `../evals.json`. They share
one `node_modules` (installed here, in this folder) so each fixture stays tiny.

| Fixture | Tests | Starting point |
|---|---|---|
| `greenfield/` | direction-setting, anti-generic, the verify loop | empty `App.tsx`, no tokens |
| `established/` | `inspect.py` → *match* existing conventions | warm palette, Fraunces + IBM Plex, `rounded-md`, hairline borders, `Button`/`Switch`/`Card`/`Field` primitives, a `/settings/profile` page showing the form convention |
| `generic/` | critique + one deliberate move away from the template look | a deliberately AI-default marketing page (indigo, gradient blob, icon-in-circle cards, fake logos and stats) |

## Running a fixture

Fixtures are pristine templates. Never work in them directly — copy one to a work
directory, link the shared dependencies, and run the dev server there:

```bash
cp -r evals/fixtures/established /path/to/work/project
ln -s "$(pwd)/evals/fixtures/node_modules" /path/to/work/project/node_modules
cd /path/to/work/project && npm run dev -- --port 5173
```

Install the shared dependencies once: `cd evals/fixtures && npm install`.
| `nextjs/` | Next.js App Router smoke test for `render.mjs` + `inspect.py` (`npm install` inside it; not part of the graded evals) | same Maple Books tokens in `app/globals.css`, `next/font` faces |
| `review/` | the review/fix path (eval-5): a working 等位通 admin queue page with nine planted defects — gray-400 text, 20px unnamed icon buttons, `focus:outline-none` nav, a nine-column table that overflows at 375, zoom blocked, a pulsing dot without a reduced-motion rule, h1→h3, an avatar without alt, status by colour alone | Tailwind utilities only, no tokens |
| `nuxt-app/` | `inspect.py` on Nuxt 4 + Nuxt UI (checked in CI; not installed, not rendered) | file routes under `app/`, a `dashboard` layout picked by `definePageMeta`, named and global middleware, `server/api`, `defineProps` in the typed and object forms |
| `vue-app/` | `inspect.py` on Vue + Vite + vue-router (checked in CI; not installed, not rendered) | a route table with lazy imports and a redirect, a slot wrapper every view sits in, a Pinia store with a localStorage key |
| `sveltekit-app/` | `inspect.py` on SvelteKit 2 + Svelte 5 + Tailwind 4 (checked in CI; not installed) | route groups `(app)` / `(marketing)` with a layout that loads data, `+page.ts` / `+page.server.ts` with form actions, `hooks.server.ts` guarding `/settings`, a `+server.ts` endpoint, `$props()` and `export let` components, mode-watcher |
| `astro-app/` | `inspect.py` on Astro 7 with plain CSS (checked in CI; not installed) | file routes and an endpoint, a layout pages sit in, two content collections, a React island (`client:visible`), middleware guarding `/drafts`, `[data-theme]` dark mode set by an inline script |
| `angular-app/` | `inspect.py` on Angular 21 + Angular Material (checked in CI; not installed — `npm install --legacy-peer-deps` and `ng serve` render it) | a route table with lazy components, a lazy NgModule with a routing module and a class guard, routes as a default export, a shell layout with an outlet, a functional guard reading a localStorage session, a service calling `/api` through a proxy, signal inputs and outputs, an M3 theme with a `.dark-theme` class set by a theme service, a tsconfig path alias |
| `static-site/` | `inspect.py` on a hand-written site (checked in CI; serve it with `python3 -m http.server`) | four pages with the header and nav copied into each (the active item differs) and one footer that differs, Bootstrap 5.3.3 from jsDelivr, Alpine from `vendor/`, a `[data-theme]` dark mode set by an inline script from localStorage |
| `eleventy-site/` | `inspect.py` on Eleventy 3 (checked in CI; not installed) | `src/` as the input folder, a permalink, a directory data file that sets the layout and tags of `blog/`, a layout chain (`post.njk` in `base.njk`), site data, a feed that is not a page |
| `jekyll-site/` | `inspect.py` on Jekyll (checked in CI; not installed) | `permalink: pretty`, `defaults` that give posts their layout, a layout chain, includes, `assets/main.scss` with front matter and a `_sass/` partial with a Sass colour variable, plugins without a Gemfile |
| `laravel-app/` | `inspect.py` on Laravel 12 + Livewire + Flux + Fortify + Inertia (checked in CI; not installed) | `Route::view`, controller routes, a Livewire page class, an Inertia page, groups with middleware and a prefix, a redirect, a required `auth.php`; controller middleware in a constructor (`except`) and in `middleware()` (`only`); `@extends` and component layouts, a class layout component, Blade components with `@props`, Fortify's views, `@vite`, `@fluxAppearance` |

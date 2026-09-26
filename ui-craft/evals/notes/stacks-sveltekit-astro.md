# SvelteKit and Astro (0.13.0, 2026-09-26)

The first sprint of adding web stacks, in the order set by the comparison with
ui-ux-pro-max: the stacks whose pages the renderer can already load, where what is
missing is reading the project. Svelte and Astro were detected before this, and
nothing more.

## The material

| | what | why |
|---|---|---|
| SvelteKit demo | `sv create --template demo`: SvelteKit 2.63, Svelte 5.56, Vite 8, plain CSS | the official starter: colocated components, `+page.ts` render options, a form action |
| Astro blog | Astro 7.3 with mdx and sitemap, laid out like the official blog template (which downloads from GitHub, blocked here), with a `[data-theme]` dark mode set by an inline script | layouts, a content collection, plain CSS variables |
| Starlight | `@astrojs/starlight` 0.42, a docs site with a splash page | a kit that draws the pages itself |
| `evals/fixtures/sveltekit-app` | Tailwind 4, mode-watcher, route groups, a layout that loads data, hooks guarding `/settings`, an endpoint, both prop styles | CI |
| `evals/fixtures/astro-app` | the blog plus a React island, middleware guarding `/drafts`, a second collection | CI |

## The inspector, before and after

On the SvelteKit demo, 0.12.2 listed seven "pages": the layout, the header and the
counter among them. It found no routes, no layout, no data loading and 0 components.
Now it lists the four pages with their routes, what loads each one's data and its
render options (`prerender true`, `csr dev`), the one form with its actions, and the
root layout with its stylesheet and chrome (`Header`).

On the Astro blog it found the pages but not the layout they sit in, the collection or
the dark mode, which is plain CSS. Now each page line says `inside BlogPost` (or
`inside Layout`, the name the page imports it under), the collection is named with its
folder, and the theme line reads: `[data-theme=dark]` on `<html>`, set before paint by
the inline script in `BaseHead.astro` (localStorage `theme`). On Starlight it found no
pages at all: Starlight builds them from `src/content/docs/`. It now lists those files
as pages, with the splash template marked.

## The renderer on the real projects

All three render without change to the audits. Two things differed from a React app:

- **Astro's dev toolbar** (`astro-dev-toolbar`) sat at the bottom of every screenshot,
  like the Nuxt and Vue devtools before 0.12.0. It is hidden now.
- **SvelteKit's framework traffic**: `__data.json` after a client-side navigation, and
  `/_app/` in a preview build, now count as framework requests; so do Astro's `/_astro/`
  assets.

Dark mode worked on the first try on both Astro sites (attribute mode: all six dark
screenshots dark). The SvelteKit demo has no dark mode.

## Found on the way

- `astro dev` stopped with "Dev server process exited before becoming ready" and
  nothing else. `npx astro sync` printed the cause: a Starlight sidebar group in the
  syntax removed in 0.39. Both facts are in `astro.md`.
- Astro's dev server outlived killing its `npx` process group; stop it by the port.
- The Nuxt reading list's auto-imported components came out in a different order on
  different runs when two had the same count (a `set` iterated under hash
  randomisation). Ties now sort by path, and the output is the same on every run.
- On every other project checked (Sunnote, the Next.js blog, TailAdmin Vue, the
  React, Next, Nuxt and Vue fixtures) the inspector's output is byte-for-byte the same
  as before.

## Not measured yet

No agent has done a task on these stacks. The next trial on a new stack should be a
match task on SvelteKit or Astro, the way the eighth trial took the archive task to
Nuxt.

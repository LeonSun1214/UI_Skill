# Astro

Read when `inspect.py` says the stack is Astro. What differs from a React project, and what to do about it.

## Where things are

- Routes are files under `src/pages/`: `.astro`, `.md`, `.mdx`. `index` is the folder's route; `[slug].astro` and `[...slug].astro` are parameters, which a static site lists in `getStaticPaths`. A `.ts` / `.js` file there is an endpoint (`rss.xml.js`). A file or folder starting with `_` is not a route.
- An `.astro` file is a frontmatter script between `---` fences, which runs on the server, then markup. Props come from `Astro.props`, typed with `interface Props`. A layout in `src/layouts/` wraps a page that places its content inside the layout tag: the inspector says "inside BlogPost" on the page line. A new page uses the same layout.
- Content lives in collections (`src/content.config.ts`, `defineCollection` with a `glob` loader): an entry is a Markdown file, and pages read them with `getCollection` and `render`. New content is a new file, not new markup.
- React, Vue or Svelte components render to static HTML unless the tag carries `client:load`, `client:idle` or `client:visible`: only those islands are interactive, so a hover or a state change written in JavaScript exists only there. The page line lists the islands.
- Styles: a `<style>` in an `.astro` file is scoped to it (`is:global` escapes). Many Astro sites use plain CSS custom properties (`:root`, `[data-theme]`) instead of Tailwind: use the project's variables (the inspector's *Declared tokens*), not new ones.

## Starlight

When the stack line says `integrations starlight`, every file in `src/content/docs/` is a page, and Starlight draws the layout, the sidebar, search and the theme. A new page is a new Markdown or MDX file there, built with its components (`Card`, `CardGrid`, `Tabs`, `Aside`, `Steps` from `@astrojs/starlight/components`). The sidebar is in `astro.config.*`: since Starlight 0.39, a group is `{ label, items: [{ autogenerate: { directory } }] }`. Theme it through `customCss` and its `--sl-color-*` properties, not by overriding its classes.

## Serving and rendering

- `npm run dev` (`astro dev`) listens on :4321.
- If it stops with only "Dev server process exited before becoming ready", run `npx astro sync`. It prints the real error, usually an integration's configuration.
- Its dev server keeps running after its `npx` process is killed: stop it by the port (`kill $(lsof -ti :4321)`).
- Astro's dev toolbar floats at the bottom of the page; the render hides it, and it is not in the screenshots.
- Pages are built on the server from collections and frontmatter, so the `requests` line reads *none from the app*. There is nothing to mock: the data are files.

## Dark mode

Often an inline `<script is:inline>` in the head component: it reads localStorage (`theme`) and sets `data-theme` or `.dark` on `<html>` before paint. Starlight uses `data-theme` and localStorage `starlight-theme`. The render's dark pass handles both.

## Checks

`npx astro check` (it asks to install `@astrojs/check` and `typescript` when missing) and the project's lint script, after the last render. `npx astro sync` regenerates the collection types after a schema change.

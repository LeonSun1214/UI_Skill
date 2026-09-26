# SvelteKit

Read when `inspect.py` says the stack is SvelteKit (or Svelte). What differs from a React project, and what to do about it.

## Where things are

- Routes are folders under `src/routes/`. In each: `+page.svelte` is the page; `+page.ts` loads its data on the server for a first load and in the browser after a navigation, `+page.server.ts` always on the server (secrets, the database, form `actions`); `+layout.svelte` wraps every page at and below its folder; `+server.ts` is an endpoint; `+error.svelte` the error page. `[slug]` is a parameter; a `(group)` folder groups routes without changing the URL, and usually shares a layout. A new page is a new folder with a `+page.svelte`; there is no route table.
- Other `.svelte` files beside a route are that route's components, not pages. Shared ones live in `src/lib/` and are imported as `$lib/components/X.svelte`.
- Props: Svelte 5 declares them with `let { title, items = [] }: Props = $props()` and renders children with `{@render children()}`; Svelte 4 with `export let title` and `<slot />`. The inspector lists each shared component's props: write the new component the way the others are written.
- Styles are Tailwind classes, or a `<style>` block in the component, scoped to it (`:global(...)` escapes the scope). Global CSS is imported once, in the root `+layout.svelte`.

## Serving and rendering

- `npm run dev` (`vite dev`) listens on :5173. Pages are server-rendered, then hydrated.
- On a first load, `load` runs during the server render, so the `requests` line reads *none from the app*: the data comes from `load` and `+server.ts`, which the dev server serves. Start it, don't mock it. After a client-side navigation SvelteKit fetches `__data.json`; the render counts that as framework traffic.
- `src/hooks.server.ts` runs before every request. The inspector names the paths it guards: a render there needs the session cookie (`--cookie` / `--storage-state`).
- Form errors come back through `form` (from `fail(400, { … })` in `actions`): render the error state with `--act` (`type:` then `press:Enter`), not by editing the action.

## Dark mode

Usually `.dark` on `<html>`, set before paint by mode-watcher (`<ModeWatcher />` in the root layout, localStorage `mode-watcher-mode`) or by an inline script in `src/app.html`. The render's dark pass handles both. To render dark on purpose, `--init-script` a file that sets the storage key.

## Checks

`npm run check` (`svelte-kit sync && svelte-check`), and the project's lint script, after the last render. The Svelte compiler reports accessibility warnings (`a11y_*`: a click handler on a `<div>`, an image without `alt`) in the dev server's log and in `svelte-check`: read them, they cost nothing.

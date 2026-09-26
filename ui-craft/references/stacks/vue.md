# Vue (Vite, vue-router)

Read when `inspect.py` says the stack is Vue. What differs from a React project, and what to do about it.

## Where things are

- Pages are views, usually `src/views/*.vue`, and the route table is `src/router/index.ts` (`routes: [{ path, component }]`). A new page needs both: the view, and a route entry in the same style (lazy `() => import('../views/X.vue')` or a static import, whichever the file uses).
- Components are imported explicitly (`import X from '@/components/X.vue'`) and written with `<script setup>`; their props are in `defineProps`. The inspector lists the most-imported ones with their props.
- Many Vue apps put the chrome in a wrapper component that every view places itself inside (`<AdminLayout>…</AdminLayout>`). The inspector says "inside AdminLayout" on each page line: a new view uses the same wrapper, and its content goes in the wrapper's slot.
- A component kit (Element Plus, Vuetify, PrimeVue, Naive UI) is on the stack line when the project uses one: build with its components, as a React project's `Button` would be reused.
- Styles are Tailwind classes in templates. `<style scoped>` blocks hold component-local CSS; they are not part of the project's vocabulary.
- State lives in Pinia stores (`src/stores/`); state that persists is in localStorage under the key the inspector names. Seed it with `--init-script` to render a populated page.

## Serving and rendering

`npm run dev` (Vite) listens on :5173. Vue renders in the browser, so the `requests` line lists the page's calls and `--mock` answers them. The Vue DevTools plugin (`vite-plugin-vue-devtools`) floats a panel over the page; the render hides it.

## Dark mode

Usually a class on `<html>`, set by a theme store or provider from localStorage. The render's dark pass adds `.dark` when the CSS has class-based dark rules; seed the storage key when the app sets the class only from its own state.

## Checks

`vue-tsc --noEmit` (or the project's `type-check` script) and its lint script, after the last render. `scripts/harness.mjs` (a component rendered alone) is React-only.

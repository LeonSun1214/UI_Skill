# Vue and Nuxt (0.12.0, 2026-09-26)

Until 0.11 the skill read React projects well and anything else loosely: `inspect.py`
detected Vue and Svelte, but its reading list, page lines, layouts and routes were
built from JSX, the App Router and react-router. This pass takes two real templates
and two fixtures through the inspector and the renderer, fixes what they showed, and
writes down what an agent needs to know about each stack.

## The material

| | kind | what it exercises |
|---|---|---|
| Nuxt UI SaaS template | Nuxt 4, Nuxt UI 4.11, @nuxt/content, 9 pages | file routes, 3 layouts, auto-imported components, Nuxt UI's colours and components, content collections, color-mode |
| TailAdmin Vue | Vue 3 + Vite + vue-router, 17 views | a route table with lazy imports, the wrapper component each view sits in, `defineProps`, localStorage state, Vue DevTools |
| `evals/fixtures/nuxt-app` | static tree, not installed | a named layout, named and global middleware, `server/api`, `defineProps` in the typed and object forms |
| `evals/fixtures/vue-app` | static tree, not installed | a route table with a redirect, a slot wrapper, a Pinia store with a storage key |

The fixtures are what CI checks the inspector on (15 assertions); the templates
are where the numbers below come from.

## The inspector

On the SaaS template the reading list now opens with Nuxt UI (colours `primary: blue`,
`neutral: slate` from `app/app.config.ts`, and its 14 most-used components), then the
auto-imported components by use, one line per page with the components its template
uses and where its data comes from (`data: content posts`), the file routes including
the parent route that wraps its children, and what runs before a page: color-mode's
class and storage key, `app.vue`, each layout with the pages that pick it
(`auth.vue` wraps login and signup), the content collections, the dev port. It takes
0.07 s.

On TailAdmin: the router table (17 routes), and on each page line "inside
AdminLayout", with the wrapper's path and role once, not on all 14 lines (the output
is 11 % shorter for it), the most-imported components with their props, and the two
localStorage keys (`theme`, `rtl_mode`).

## The renderer

The SaaS template's `/pricing` on `nuxt dev`, before and after:

| finding | 0.11.6 | 0.12.0 | what it is |
|---|---|---|---|
| "Monthly" 1.1:1 | FAIL | passes | white text on the tab's sliding indicator, an absolutely positioned layer the old measurement did not see |
| nav links Docs, Pricing | focus invisible | ring 1.35:1 (outline on `::before`) | Nuxt UI draws the ring on a pseudo-element, in primary at 25 % |
| the newsletter input | "fill 1:1" | "ring 1.49:1" | outlined by an inset box-shadow ring, not a border |
| 2 elements | focus obscured by `nuxt-devtools-frame` | none | the DevTools panel, now hidden like the error overlays |
| requests | 4 listed, "what a second render would --mock" | none from the app, 4 of the framework's own counted | the build manifest, the payload, @nuxt/content's database |
| "Get Started" 3.76:1, "SaaS" badge 3.33:1, faint rings 1.35:1 | reported | reported | real: Nuxt UI's defaults (white on the 500 shade, `outline-primary/25`) |

The ring parser was wrong for every Tailwind project, not only Nuxt: Tailwind
composes `box-shadow` from five layers, most of them `rgba(0, 0, 0, 0)`, and the old
code measured the first colour in the string. A Tailwind v4 ring was never measured;
a v3 ring with an offset measured its white offset, 1:1. Now each layer is read, the
most visible one counts, a drop shadow that was there before focus is not taken for
a ring, and a border recoloured on focus counts with it.

The positioned layer counts only when it paints under the text: the text must sit
in a positioned box that comes after it (or the layer has a negative z-index). A veil
over static text paints over it, so that text still fails; an image under a veil
leaves no single colour, so the text on it is unverifiable, not a 1:1 failure.

`selftest/layers.html` plants each case. On it the 0.11.6 renderer made five false
reports (the tab label, the text on the photo at 1:1, a well-ringed field as "fill
1:1", a strong `::before` ring as invisible, a field whose focus is a strong border
plus a faint glow as a faint ring), two wrong attributions (a faint `::before` ring
as invisible, a faint-ringed field as "fill") and one miss (a faint shadow ring).
0.12.0 reports exactly the five planted defects and counts the photo as
unverifiable. 27 self-test checks pass.

React pages: Sunnote (Vite, Tailwind 3) and three pages of the Next.js blog
(Tailwind 4) give the same findings under both renderers; the requests line's wording
is the only difference, and on the blog Next's `__nextjs_original-stack-frames` call
is now counted rather than listed.

A render of `/pricing` takes about 16 s on the dev server: Vite streams modules after
load, so network idle never comes and each viewport waits out its limit. TailAdmin
takes 10 s.

## What is not measured

No fresh agent has done a task on a Vue or Nuxt project yet: the reading list is
checked for content, not for what an agent does with it. The description now names
Vue and Nuxt; the trigger eval was not rerun. `harness.mjs` (a component rendered
alone) stays React-only.

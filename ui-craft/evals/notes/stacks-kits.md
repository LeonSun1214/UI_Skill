# Component kits: MUI, Ant Design, Chakra, Element Plus, Vuetify, styled-components, CSS Modules (0.16.0, 2026-09-26)

The last part of the first tier. These are React and Vue projects without Tailwind, or with
Tailwind barely used, where the look is a theme object and the kit's components. The
inspector named the kit and read nothing else; its React pages were whatever sat in a
page folder.

## The material

| | what | why |
|---|---|---|
| material-kit-react | `minimal-ui-kit/material-kit-react`, MUI 7, React Router 7, Vite | a theme split over `src/theme/`, `sx` in 54 files, routes in a `RouteObject[]` handed to `createBrowserRouter`, thin pages rendering views through barrels |
| Horizon UI | `horizon-ui/horizon-ui-chakra`, Chakra 2, Create React App, React 19 | `extendTheme` merged from files, `useColorModeValue` in 58 files, a `routes.js` menu mounted under `admin/*` layouts |
| Ant Design Pro | `ant-design/ant-design-pro`, antd 6, umi 4, Pro components | `config/routes.ts`, tokens in the umi config and ProLayout settings, a mock API and mock sign-in, 27 routed pages |
| Outline | `outline/outline`, styled-components 5 | a theme built from a colour object, a dark theme picked from a stored choice, react-router v5 routes to lazy scenes through a namespace import |
| vue-manage-system | `lin-xin/vue-manage-system`, Element Plus 2.6 | the default theme with a runtime colour picker, hash history, webpack-commented imports |
| RuoYi-Vue3 | `yangzongzhuan/RuoYi-Vue3`, Element Plus 2.13 | routes the backend's menu adds at runtime, extensionless imports, `useDark` with Element Plus's dark variables |
| Berry | `codedthemes/berry-free-vuetify-vuejs-admin-template`, Vuetify 4 | a theme definition with component defaults, file routes |
| seven fixtures | `mui-app`, `antd-app`, `chakra-app`, `styled-app`, `cssmodules-app`, `element-app`, `vuetify-app` | CI |

## The inspector, before and after

Before, material-kit-react had "none declared" for tokens and Tailwind-style radius counts.
It listed three routing helpers (`src/routes/components/error-boundary.tsx`,
`router-link.tsx`, `sections.tsx`) as pages. Horizon was greenfield with dark mode "not
used". Ant Design Pro's pages included every component folder under `src/pages`, and its
verdict read "Dominant hue: zinc (1 uses)" from one Tailwind class. vue-manage-system's
verdict said "Shadow: shadow (default) dominant": 45 of Element Plus's `shadow="hover"`
props. Outline's three route files were its pages.

Now each report has the kit's theme under *Declared tokens*: MUI's palette (`primary
#1877F2` …), radius 8, fonts and 12 overrides; Horizon's brand scales and 10 component
styles; Ant Design Pro's `colorPrimary`, ProLayout settings and `AlibabaSans`; Outline's
colours led by `accent #0366d6` and its `buildDarkTheme`; Berry's `PurpleTheme` and its
defaults (`VCard rounded md`, outlined fields). Each has a line of the kit's components by
use, what a match task builds with, and how dark mode switches, with the flag:
`--dark-storage chakra-ui-color-mode=dark`, `vueuse-color-scheme=dark`, `theme=dark`.

React pages come from the route table: material-kit-react's six (with DashboardLayout or
AuthLayout, and the view each thin page renders), Ant Design Pro's 27 (sign-in included,
`access canAdmin`, the ProLayout), Horizon's six from its menu table under their layouts,
Outline's scenes. Sunnote's pages gained routes and their AppShell. Sunnotice kept its four
sign-in screens, which `App` shows before any route, marked "no route: `src/App.tsx`
shows it".

Found and fixed on the way:
- material-kit-react's thin pages render their views through barrels, one of them aliased
  (`OverviewAnalyticsView as DashboardView`). The page line follows both.
- Outline's scenes are `Scenes.Drafts.Component` from `import * as Scenes`.
- Horizon's route paths are the menu's `layout` plus its `path`, and a layout route is a
  splat (`admin/*`). The splat is now the layout of the routes under it, not a page.
- Ant Design Pro's sign-in page fell off the end of the 24-line cap. Pages from a route
  table may take 32.
- Its dependencies were read from the folder above (umi was no known framework), and
  `Welcome.tsx` was taken for a splash screen.
- RuoYi's route imports have no extension (`@/views/login`), and vue-manage-system's carry
  a webpack comment. Both resolve now.
- Vue files were left out when looking for the key a theme choice is stored under.

## What rendering showed

- **MUI's focus ripple.** On focus MUI mounts a ripple element, a circle of
  `currentColor` at 30%, a frame after the re-render. The renderer compared only layers
  that existed before focus, so 11 of 22 tab stops read as "focus invisible". A layer that
  appears inside the control is now measured, and the walk waits two frames after each
  Tab. Result: 20 of 22 visible, 9 of them faint (1.47–2.69:1). The two left are real: the
  workspace button changes nothing on focus, and one icon button has no ripple.
- **Vuetify's overlay.** Vuetify raises a real overlay element to 12% opacity, not a
  pseudo-element, so the tint read as 1:1. Inner elements' own background and opacity are
  now part of the layers: 1.23–1.3:1.
- **Dark passes on apps without dark mode.** MUI's light-only theme writes
  `[data-color-scheme="light"]` rules, and Element Plus's stylesheet has one widget rule
  under `.dark` (the colour picker). Both started a dark pass that repeated every light
  finding as a dark one. The attribute must now name `dark`. Descendant-only `.dark` rules
  count from three on, since a stylesheet written for a dark class has many.
- **A dark pass that moves nothing.** Vuetify writes variables for its built-in dark theme
  even when the app never uses it, and the app root carries its own theme class. A dark
  class on `<html>` changed nothing, and the pass reported 20 contrast failures twice. Such
  a pass is now said once, as a pass that moved nothing, and not counted.
- **Chakra through its own switch.** With the flag the inspector prints
  (`--dark-storage chakra-ui-color-mode=dark`), Horizon renders dark (`#F4F7FE` →
  `#0B1437`) with no dark contrast failures. Without it, the pass moves nothing and says so.
- **Covers and widgets.** At 375 Berry opens its navigation drawer over the header. Tab
  reaches the header's buttons underneath, reported as "behind svg". The cover is now named
  by its layer ("behind nav.v-navigation-drawer"), and at 768 by the drawer's scrim. A
  `v-select`'s own shown value over its input is no longer a cover.
- **Tonal icon buttons.** Berry's icon buttons share their card's fill (1:1), and nine
  failed non-text contrast. Their white icon identifies them, so they are warned, like a
  text button on a faint fill.
- **Layout grids.** MUI's dashboard Grid (spans 3, 4 and 8) was flagged as a ragged row.
  Items of different widths are a layout; Sunnote's wrapping chips stopped being flagged
  for the same reason.
- **A cold Vite server.** Berry's first render timed out: Vite found new dependencies on
  the first request and reloaded the page mid-load. The load is retried once, and the
  output says so.
- **A blocked font host.** Ant Design Pro's `AlibabaSans` comes from a host blocked here.
  The fonts line said so, and the Verified block said "all loaded". It now counts the
  face as not loaded.
- **A mock session.** Signing in to Ant Design Pro with `--save-state` wrote an empty file:
  the mock keeps the session in the server. The output now says the file holds nothing.

The kits' own defaults, as measured (each in `references/stacks/kits.md` with its fix):
- **MUI:** the focus ripple is faint; grey-500 captions are 2.73:1.
- **Ant Design:** the focus outline `#91caff` is 1.74:1; secondary text is 3.36:1; white on
  `#1677ff` is 4.10:1.
- **Element Plus:** `#409eff` is 2.78:1 for white text, links and the input's focus ring.
- **Vuetify:** the focus overlay is about 1.25:1.
- **Horizon UI:** its theme sets `_focus: { boxShadow: 'none' }` on every Button.

## Checked for regressions

- The inspector's markdown is the same on the Nuxt, Vue, Astro and Angular projects and on
  ten of the eleven older fixtures. It changed on:
  - Sunnote, Sunnotice and the established fixture: pages from their route tables;
  - the Next.js blog and boilerplate: a thin page names what it renders;
  - the SvelteKit demo: its font package is named.
- The renderer's findings are the same on Sunnote `/` and `/new`, TailAdmin Vue `/signin`
  and `/`, and the review and established fixtures, with three changes:
  - Sunnote's wrapping chips are no longer a ragged row;
  - TailAdmin's collapsed sidebar icon button is a weak surface, not a failure;
  - the weak-surface heading is reworded.
- Self-test: 36 checks (a kit page and an echo page). CI: 45 new assertions on seven
  fixtures.

## Not measured yet

No agent has done a task on a kit project. A match task on material-kit-react (a new
dashboard card) or Ant Design Pro (a new list page from `ProTable`) would show whether the
kit line and the theme are read before hand-rolled markup is written.

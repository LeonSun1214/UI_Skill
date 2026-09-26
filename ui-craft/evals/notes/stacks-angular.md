# Angular (0.14.0, 2026-09-26)

The third stack of the first tier, after SvelteKit and Astro. Angular was detected before
this, and nothing more: its pages are components a route table names, not files, so none
of the readers that find pages by path found any.

## The material

| | what | why |
|---|---|---|
| demo | Angular 21 from `ng new`, Material 21 from `ng add`, pages from Material's schematics (navigation, dashboard, table, address form), then routes, a guard, a service, a proxy and a theme service written the way the CLI's docs write them | standalone components, lazy routes, an M3 theme, `.dark-theme` |
| RealWorld | `gothinkster/angular-realworld-example-app`, Angular 21 | plain CSS, `loadComponent` with default exports, inline templates, a guard declared in the routes file, an interceptor that sets the API host |
| ng-matero | `ng-matero/ng-matero`, Angular 21 + Material 21 | tsconfig path aliases and barrels, 60 pages, a guard behind a token service, `angular-in-memory-web-api`, `.theme-dark` on `<html>`, scrolling inside `mat-sidenav-content` |
| TailAdmin | `TailAdmin/free-angular-tailwind-dashboard`, Angular 22 + Tailwind 4 | 139 components, eager routes, a theme service that sets `.dark` and a body class |
| NgModule starter | `tomastrajan/angular-ngrx-material-starter`, Angular 12 | NgModules, lazy modules with routing modules, a class guard re-exported by a module, four Material M2 themes, the app under `projects/` |
| `evals/fixtures/angular-app` | the demo grown: a lazy NgModule with a class guard, routes as a default export, a path alias | CI |

## The inspector, before and after

On all five, 0.13.0 found no pages, no routes and (outside `components/` folders) no
components. On the demo it called an Angular Material app greenfield, said dark mode was
not used, took its vocabulary from component stylesheets that only style their own
component (`.row`, `.col` from the settings form), and named the dark class `.dark` when
it was `.dark-theme`. "Imported most" was a list of model files.

Now each project's report has one line per page with its route and the layout whose
`<router-outlet>` holds it, and the route table with lazy entries marked. The three
guards found (the demo's functional `authGuard`, RealWorld's `requireAuth` declared in
the routes file, ng-matero's `authGuard` behind the `@core` barrel) each come with the
pages they cover, where they redirect and the session they read: localStorage
`ng-demo-token`, localStorage `jwtToken`, storage key `ng-matero-token` (through ng-matero's
storage service). The page lines name the requests each page makes through its services
(RealWorld's article page: `GET /articles/{slug} (ArticlesService.get)`, the comments, the
delete). Components are listed by selector with inputs and outputs
(`<app-button>`: size, variant, disabled, className, startIcon, endIcon; outputs btnClick).
Material's theme is read in both generations: M3 `mat.theme` with its palettes, and the M2
starter's four themes with `indigo` / `light-blue` / `pink`. The dark class and the service
that sets it are named, with the flag to render dark through it.

The starter's `AuthGuardService` is re-exported by `core.module.ts` (`export { … }` of an
imported name); following that took one more case in the barrel reader. ng-matero keeps a
copy of its theme under `schematics/`; the reader now prefers the one under the app's
source root.

## What rendering showed

The renderer loaded every page without change; what it measured on Material was wrong in
four ways, and one more thing surfaced on TailAdmin.

- **Screenshots after the walks.** The sign-in page's fields were red in every
  screenshot: the Tab walk had focused and left them, Angular marked them touched, and
  empty required fields show their error. The screenshots are now taken first. A walk
  that leaves fields invalid sends the dark pass to a fresh load. Angular without zone.js
  applies `ng-touched` a frame after blur, so the check waits two frames: read at once,
  it missed the change on one viewport in three runs.
- **Focus beside the control.** A Material field shows focus on the three pieces of its
  notched outline, which sit next to the input, not around it: "focus invisible" on every
  field. Those pieces are now read (`border of its frame`).
- **Focus as a tint.** A Material button, list item or nav link shows keyboard focus as a
  state layer: a child's `::before` fading to 12% opacity. Before, that read as "focus
  invisible"; now it is measured (1.2–1.4:1 on the demo's and ng-matero's buttons, list items and
  links; 2.1:1 on ng-matero's slide toggle) and reported as a faint ring (`tint on an inner
  layer`). With `@include mat.strong-focus-indicators()`
  Material draws a 3px ring on another child's `::before`. That ring is now read
  (`ring on an inner layer`), and the demo's dashboard went from 9 faint rings to 9 of 9
  at 3:1 or more, light and dark. Hover had the same blind spot: it now reads the inner
  layers' pseudo-elements, and "no hover feedback" on Material buttons went away.
- **Dark classes.** Only `.dark` was put on the page. `.dark-theme` and `.theme-dark`
  (with `color-scheme: dark`, which Material's `light-dark()` colours follow) are now found
  in the stylesheets, and `color-scheme: light dark` counts as dark support. TailAdmin
  loads ApexCharts, whose `.apexcharts-theme-dark.apexcharts-canvas` rule sets a variable.
  A prefixed name counts only as the whole first compound of a rule that sets custom
  properties or `color-scheme`, so a widget's variant is left alone.
- **A scrolling pane.** ng-matero scrolls inside `mat-sidenav-content`. The walks scrolled
  it, `window.scrollTo(0, 0)` did not undo that, and the 375 dark screenshot opened at the
  Chips section. The pane is now scrolled back.
- **A theme service.** TailAdmin's service adds `.dark` to `<html>` and a background class
  to `<body>`. With only `.dark`, the dark pass measured light text on a white body: 40
  contrast failures. `--dark-storage theme=dark` sets the app's stored choice and reloads,
  so the service runs: 3 failures, all real.

## Found on the way

- `ng new` with the Angular 21 CLI failed in npm's resolver (`Cannot read properties of
  null (reading 'edgesOut')`, in the peer set of vitest and jsdom); `npm install
  --legacy-peer-deps` installs it. The Angular 22 CLI refuses Node 22.22.2 and names the
  versions it needs; TailAdmin was served with Node 22.22.3 unpacked into the scratchpad.
- RealWorld's only global stylesheet is in a git submodule that a clone does not fetch.
  The build stops without it, and the inspector now says so.
- Google Fonts does not load in this sandbox (`ERR_CERT_AUTHORITY_INVALID`). Pages render
  in fallback faces and Material icons show their names (`more_vert`); the `fonts:` line
  now says why, so the names are not taken for a bug.
- `setsid nohup … & echo $!` printed the pid of a process `setsid` forked away from.
  Stopping `ng serve` by that group did nothing: stop it by the port's process group.

## Checked for regressions

- The inspector's output on Sunnote, the Next.js blog, TailAdmin Vue, the Nuxt SaaS
  template, the SvelteKit demo, both Astro sites and the eleven other fixtures is
  byte-for-byte the same, except Sunnote's "imported most" counts, which no longer count
  test files.
- The renderer's findings are unchanged on the review, established, Next.js and Nuxt
  fixtures, on three TailAdmin Vue pages (a chart's random id aside) and on five Sunnote
  pages, two of them forms.
- Self-test: 30 checks (a Material page and a stored-theme page added). CI: 15 new
  assertions on the Angular fixture, 55 in all, passing locally.

## Not measured yet

No agent has done a task on Angular. The next trial on a new stack should be a match task
on an Angular Material app, where the one-line focus fix is the kind of thing a first
render finds.

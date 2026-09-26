# Angular

Read when `inspect.py` says the stack is Angular. What differs from a React project, and what to do about it.

## Where things are

- A page is a component that a route names. The route table is `app.routes.ts` (standalone components, Angular 17+) or an `*-routing.module.ts` (`RouterModule.forRoot` / `forChild`, NgModules). `loadComponent` and `loadChildren` load a page lazily; `children` put pages inside the parent component's `<router-outlet>`, which makes that parent a layout. The inspector follows the table, lazy modules included, and prints one line per page with its route and the layout it sits in. A new page is a component plus a route entry: file names do not make routes.
- A component is a class under `@Component`. Its markup is `templateUrl` (an `.html` beside it) or an inline `template`; its styles are `styleUrl` / `styleUrls`, scoped to it (`:host` styles the element itself). Global styles are the files `angular.json` lists under `styles`, usually `src/styles.scss`: the inspector's vocabulary comes only from those, and from components that turn scoping off.
- Components are used by selector (`<app-stat-card>`). A standalone component must be in the `imports` of each component that uses it; in an NgModule app, in the module's `declarations` or `imports`. A missing one fails the build with "is not a known element".
- Inputs are `label = input.required<string>()` and `value = input(0)` (signals: read them as `label()` in the template), or `@Input() label` in older code. Outputs are `selected = output<string>()` or `@Output() selected = new EventEmitter<string>()`. The inspector lists each shared component's inputs and outputs: write a new one the way the others are written.
- Templates use `@if`, `@for (x of xs; track x.id)` and `@switch` (Angular 17+), or `*ngIf` / `*ngFor` in older code; `[prop]`, `(event)`, `[(ngModel)]`; `| async` for an observable.
- Data comes from services (`@Injectable`) that call `HttpClient`, which components `inject()`. The inspector lists each service's requests, and the page line names the calls that page makes (`data: GET /api/stats (Orders.stats)`). An interceptor can prefix a base URL or add the session header: the inspector says which.

## Angular Material

- The theme is a Sass mixin in the global stylesheet. It is `mat.theme((color: (primary: mat.$azure-palette, …), typography: Roboto, density: 0))` in M3 (Angular Material 18+), or `mat.define-light-theme` with palettes in M2. Custom styles read the theme through the `--mat-sys-*` variables (`var(--mat-sys-primary)`, `var(--mat-sys-surface-container)`, `font: var(--mat-sys-title-medium)`), never hex values. Per-component changes go through `mat.<component>-overrides((…))`.
- Build with its components (`mat-card`, `mat-form-field` with `matInput`, `matButton="filled"`, `mat-table`), each module imported (`MatCardModule`) where it is used.
- Dark mode: M3 colours are `light-dark()` values that follow `color-scheme`. An app switches with a class that sets `color-scheme: dark` (`.dark-theme`, `.theme-dark`), or follows the OS with `color-scheme: light dark`. The render's dark pass finds the class in the stylesheets and puts it on `<html>`.
- Keyboard focus on Material buttons, list items and links is only a faint state layer, about 1.2:1, and the render reports it: `focus ring <3:1 … (tint on an inner layer)`. The fix is one line in the global stylesheet, `@include mat.strong-focus-indicators();`, after which each control draws a 3px ring and the finding goes away. A field's focus is its outline thickening; the render reads it as `border of its frame`.
- `<mat-icon>` draws a ligature from the Material Icons (or Symbols) font, which `index.html` usually links from Google Fonts. Where that font cannot load (offline, a blocked host), each icon shows its name (`more_vert`). The render says so on its `fonts:` line: it is not a fault in the page.

## Serving and rendering

- `npm start` (`ng serve`) listens on :4200 (`serve.options.port` in `angular.json`, or `--port`). The first build takes a few seconds; after that a change rebuilds in about one. The Angular 22 CLI needs Node 22.22.3 or 24.15 or later: an older Node stops it with a message that names them.
- A proxy file (`proxyConfig` in `angular.json`, usually `proxy.conf.json`) sends `/api` to a backend: start the backend, or `--mock` the calls the page makes, which the inspector names.
- A guard in the route table (`canActivate: [authGuard]`) redirects a visitor without a session, and the render then shows the sign-in page. Seed the session the guard reads (the inspector names the storage key) with `--init-script`, or sign in with `--act` (`click:role=button[name="Sign in"]`, then `wait:` a selector on the page behind it). An app that answers its own HTTP calls with `angular-in-memory-web-api` needs neither a backend nor mocks.
- Forms mark a field touched when it loses focus, and the render's Tab walk would leave empty required fields in their error state. The screenshots are therefore taken before the walk, and the dark pass loads the page again. To render the error state on purpose, `--act` into the field and out of it.
- A theme service that does more than put a class on `<html>` (a body class too, a stored choice read at boot) is best rendered dark through its own switch: `--dark-storage KEY=dark` sets the stored choice and reloads. The inspector prints the flag when it finds the service.
- Many Material layouts scroll inside `mat-sidenav-content`, not the window. The render puts that scroll back after its walks, so every screenshot starts at the top.

## Checks

`npx ng build` runs the template type-check (with `strictTemplates`, a wrong input name or type fails it). Run `npx ng lint` if angular-eslint is set up: its template rules include accessibility (`alt-text`, `click-events-have-key-events`, `interactive-supports-focus`). `ng test` runs the unit tests.

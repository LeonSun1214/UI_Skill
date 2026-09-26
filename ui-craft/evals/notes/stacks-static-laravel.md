# Laravel, hand-written HTML, Eleventy and Jekyll (0.15.0, 2026-09-26)

The last two stacks of the first tier, after SvelteKit, Astro and Angular. Both are pages
that no JavaScript framework describes: Laravel's are Blade views that routes and
controllers name, and a static site's are files, or templates a generator turns into files.

## The material

| | what | why |
|---|---|---|
| Livewire starter kit | `laravel/livewire-starter-kit`, Laravel 13, Livewire 4, Flux, Fortify | `Route::livewire` with `pages::` names, layout components, Fortify's views, `@fluxAppearance`, a first run (composer, key, SQLite, Vite) |
| laravel.io | `laravelio/laravel.io`, Laravel 11, Livewire 3, Flux, Filament | controllers with constructor middleware, `except` given as an array, Tailwind 4 |
| BookStack | `BookStackApp/BookStack`, Laravel 12 | `@extends` layouts, Sass, a dark mode the server writes into `<html class>` from a user setting, 95 guarded routes |
| SB Admin 2 | `StartBootstrap/startbootstrap-sb-admin-2` | 14 hand-written pages, Bootstrap 4.6 vendored, gulp and Sass, a sidebar and topbar copied into each page |
| Landing page | `tailwindtoolbox/Landing-Page` | one page, Tailwind 2 from unpkg and jQuery from a CDN |
| Eleventy base blog | `11ty/eleventy-base-blog`, Eleventy 3 | directory data, per-page CSS bundles, a feed and a sitemap among the templates |
| Jekyll Now | `barryclark/jekyll-now` | no Gemfile, Sass partials and variables, layouts chained through front matter |
| four fixtures | `static-site`, `eleventy-site`, `jekyll-site`, `laravel-app` | CI |

## The inspector, before and after

On Laravel, 0.14.0 read `vendor/` as the project. The starter kit's vocabulary came from
a package's docs stylesheet (`vendor/league/config/docs/global.css`) and a test fixture,
its "imported most" was Livewire's own JavaScript, its strings a framework test's
dictionary, and it found no page and no route. laravel.io had "nothing to read first"
and one indigo class; BookStack was "no recognised UI stack". Now the starter kit's
report has 12 page lines, laravel.io's 16 and BookStack's 24. Each line gives the view's
routes, its middleware, the components it uses and the layout chain around it. The
report lists Flux's components by use, the Blade components with their props, the
guarded routes and how to sign in once for them, and who sets the dark class.

On static sites, 0.14.0 said "no recognised UI stack" for SB Admin 2, the landing page,
the Eleventy blog and Jekyll Now, and called Jekyll Now greenfield. SB Admin 2 now reads
as 14 pages on Bootstrap 4.6.0 (vendored) with jQuery, Font Awesome and Chart.js. Its
sidebar is copied into 11 of the 14 pages and identical in 10 once the active item is set
aside, and the line names the odd copy (`404.html:31`). The report also lists the Sass
variables its CSS is compiled from, the file to edit rather than the compiled
stylesheet. Jekyll Now reads as 4 pages with their routes and layout chains, and its
colour and font variables as tokens. It is now a site to match, not a greenfield.

Bugs found on the way, each fixed before it reached a fixture:

- SB Admin 2's sidebar first read as "different in each": the normaliser stumbled on
  quoted attributes. It now compares copies attribute by attribute, with the state
  classes and `aria-current` set aside.
- A search form in the topbar made every page a "form" page. A page's signals are now
  measured without its copied chrome.
- The Eleventy blog "loaded" `node_modules/…css`, which a Nunjucks comment mentioned,
  and listed `sitemap.xml` as a page. Template comments are stripped, and a template
  that writes XML, JSON or text is not a page.
- Jekyll's home route came out as `//`, and pages ignored `permalink: pretty`.
- Skipping `vendor/` hid SB Admin 2's vendored Bootstrap. The kit reader now looks in
  the vendor folders itself.
- laravel.io's `/forum` showed as guarded: its controller's constructor excluded it with
  `except` given as an array.
- BookStack's dark class first came out as set by `display.ts`, a script that toggles it
  at runtime. The server writes it into `<html class>` in `layouts/base.blade.php`, and
  the Blade `<html>` is now read first.
- Jekyll Now stayed greenfield after its pages were read. The verdict counted Tailwind
  classes, components and CSS variables, and a Sass site has none of them. Sass
  variables are now declared tokens, and a site whose pages share a kit, a layout, copied
  chrome or a stylesheet's classes is matched.

## What rendering showed

- **A sign-in replayed into a rate limit.** Rendering the starter kit's dashboard with
  `--act` sign-in steps signed in once per viewport, and once more for the dark pass.
  Fortify allows five a minute. After a few renders, the 375 viewport got *Too Many
  Requests*, and the render measured that page as the dashboard. `--save-state` now keeps the session the
  steps made, so a sign-in happens once, and every other page renders with
  `--storage-state`. An error status is a warning (`page answered 429`), and a viewport
  that got a different page from the others says which page it measured.
- **Steps replayed after they navigated.** The dark pass reloads the page it measured,
  which after a sign-in is the dashboard, and it replayed the steps there: `type` into an
  email field that is not on the dashboard, then "dark rule present but page colours did
  not change". Steps that changed the URL are no longer replayed.
- **A kit that never arrived.** The landing page loads Tailwind 2 from unpkg, which this
  sandbox blocks. The render measured the unstyled page: a 621px-wide layout at 375 and
  24 targets under 24px. The output now names each stylesheet and script that did not
  load before any number. Answering them from `npm pack` copies with `--mock` rendered
  the page as its visitors see it: no overflow, 11 small targets, 2 contrast failures.
- **A dark gradient.** The starter kit's sign-in page has a gradient background, so the
  dark pass compared "no colour" with "no colour" and reported the background unchanged.
  Now it says "a gradient or image".
- **An app shell as a ragged row.** Flux lays the page out as a grid on `<body>` (sidebar,
  header, main), which the ragged-row check read as three cards in two columns. A grid
  whose items are the page's landmarks is a layout, not a card row.
- **Livewire's traffic.** Livewire posts to `/livewire-<hash>/update`. It now counts as
  framework traffic, like `/_next/`, rather than an app request to mock.

The findings themselves were the templates' own. SB Admin 2 has 40 text contrast
failures: 17 are its body colour (`$gray-600`, `#858796` on white, 3.38:1), the rest its
card headings, badges and `text-white-50` captions. It also has 10 controls without
visible focus, 7 obscured and 5 unnamed. The
Eleventy blog's post: 6 contrast failures light and dark. Jekyll Now: zoom blocked, two
`h1`s. The starter kit's profile page: 2 contrast failures and a field border at under
3:1, light and dark.

## Found on the way

- `composer install` downloads packages from GitHub's archive host, which this sandbox
  blocks. `--prefer-source` clones them instead. `phpstan/phpstan` is published only as
  an archive, so it needs `--no-dev`.
- Laravel 13's Vite plugin downloads the app's fonts at build time (`fonts: [bunny(…)]`).
  Bunny's 403 here stops `npm run build`, so the starter kit was built without that
  option.
- Jekyll on Ruby 3 without a Gemfile needs `webrick` and `kramdown-parser-gfm`, plus the
  plugins `_config.yml` lists. The inspector's serve line names them.
- A fresh Laravel install has no users. The sign-in recipe in `laravel.md` creates one
  with `tinker`, including `email_verified_at` for `verified` routes.

## Checked for regressions

- The inspector's markdown on Sunnote, the Next.js blog and boilerplate, TailAdmin Vue,
  the Nuxt SaaS template, the SvelteKit demo, both Astro sites, Sunnotice, the five
  Angular projects and the eleven older fixtures is byte-for-byte the same, with two
  exceptions. The "none declared" line now also names Sass variables, and ng-matero and
  the NgRx starter gain their Sass variables (with Material's palette calls left to the
  theme line). The JSON gains five keys.
- The renderer's findings are unchanged against 0.14.0 on Sunnote `/` and `/new`,
  TailAdmin Vue `/signin` and `/` (a chart's random id aside), and the review and
  established fixtures. None of the new warnings fire there.
- Self-test: 34 checks (a blocked kit and its local copy, a saved sign-in, an error page,
  an app-shell grid). CI: 33 new assertions on the four fixtures.

## Not measured yet

No agent has done a task on Laravel or a static site. Two trials would test what this
release adds. The first is a nav change on SB Admin 2, where the report says the sidebar
is copied into 11 pages: does the change land in all of them? The second is a new page in
the Livewire starter kit, which should be built from Flux components inside the app
layout and rendered signed in through `--save-state`.

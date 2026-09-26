# Laravel (Blade, Livewire, Inertia)

Read when `inspect.py` says the stack is Laravel. What differs from a JavaScript project, and what to do about it.

## Where things are

- Routes are in `routes/web.php` and the files it `require`s (`settings.php`, `auth.php`). A route names what it shows in one of these ways: a view (`Route::view('dashboard', 'dashboard')`); a controller method that `return view('users.profile', …)`; a Livewire page (`Route::livewire('settings/profile', 'pages::settings.profile')`, `Volt::route`, or a Livewire class); or an Inertia page (`Inertia::render('dashboard')`). The inspector follows each GET route to its view file. It prints one line per view with its routes and middleware, and reads the sign-in pages Fortify registers (`Fortify::loginView`).
- A view name is a path: `users.profile` is `resources/views/users/profile.blade.php`. `pages::settings.profile` looks in a namespace folder (`resources/views/pages/`).
- Layouts: either `@extends('layouts.app')` with `@section('content')` (the layout `@yield`s it), or a layout component around the page (`<x-layouts::app>`, `<x-app-layout>`, `<x-layouts.app>`) that prints `{{ $slot }}`. A Livewire page with no layout of its own sits in Livewire's default one (`layouts::app` in Livewire 4). The page line prints the whole chain; the chrome (sidebar, header) is in the last layout.
- Blade components: `resources/views/components/button.blade.php` is `<x-button>`, and `components/forms/input.blade.php` is `<x-forms.input>`. Their props are in `@props([...])`, or in the constructor of a class in `app/View/Components`. The inspector lists them by how many views use them: build with those, not new markup.
- Flux (`<flux:button>`, `<flux:input>`) is Livewire's component kit, like Nuxt UI; the inspector counts its components. Heroicons and similar come in as `<x-heroicon-o-…>` components.
- Styles: `resources/css/app.css` (Tailwind 4 with `@theme`, or 3 with `tailwind.config.js`) or Sass in `resources/sass`, loaded by `@vite([...])` in the layout's head.

## Inertia

A route that calls `Inertia::render('dashboard')` shows a Vue or React component from `resources/js/pages/`. Read those pages as a Vue or React project would be read (`references/stacks/vue.md`); Laravel supplies their props and routes.

## Serving and rendering

- First run: `cp .env.example .env`, `php artisan key:generate`, and a database. The default is SQLite: `touch database/database.sqlite`, then `php artisan migrate`.
- `php artisan serve` listens on :8000. The assets come from Vite: run `npm run dev` beside the server, or `npm run build` once. With neither, every page fails with *Vite manifest not found*. `composer run dev` (Laravel 11+) starts the server, the queue and Vite together.
- Laravel 13's Vite plugin can download the app's fonts during the build (`fonts: [bunny('Instrument Sans', …)]` in `vite.config.js`). Where the font host is blocked, `npm run build` stops with a 403: build with the network, or take the `fonts` option out for a local build and put it back.
- `composer install` downloads packages from GitHub. Where GitHub's archive host is blocked, `composer install --prefer-source` clones them instead; it is slower, and works. A package published only as an archive (`phpstan/phpstan`, a dev tool) cannot be cloned: add `--no-dev`, which rendering does not need.
- A route with the `auth` middleware (on the route, its group, or the controller's constructor or `middleware()`) redirects a visitor without a session to `/login`. A fresh install has no users: register one on `/register`, or create one with `php artisan tinker` (`User::create([...])`, and `email_verified_at` for `verified` routes). Sign in once and keep the session: `render.mjs <app>/login --viewports 1440 --act 'type:input[name=email]=…' --act 'type:input[name=password]=…' --act 'click:button[type=submit]' --act wait:1500 --save-state .ui-craft/state.json`, then render every guarded page with `--storage-state .ui-craft/state.json`. Signing in with `--act` on every render trips the sign-in rate limit (Fortify allows five a minute), and the render then measures a *Too Many Requests* page; the output says so.
- Livewire updates the page by posting to its own endpoint (`/livewire-<hash>/update`; `/livewire/update` in Livewire 3), which the render counts as framework traffic: `--act` a click, then `wait:` for what it changes.
- Validation errors come back after a POST and a redirect. To render the error state, `--act` the form with bad input and submit it.

## Dark mode

A Tailwind app with Flux switches with `.dark` on `<html>`, set before paint by `@fluxAppearance` from localStorage `flux.appearance` (`light`, `dark` or `system`). Render dark with `--dark-storage flux.appearance=dark`. An app that stores the choice as a user setting writes the class into `<html class>` on the server: render signed in as a user with the setting on, or with `--dark`.

## Checks

`php artisan view:cache` compiles every view: a Blade syntax error or a missing component fails it. Run the project's tests (`php artisan test`), and `vendor/bin/pint` if the project uses it. After changing JavaScript or CSS, rebuild the assets with `npm run build`.

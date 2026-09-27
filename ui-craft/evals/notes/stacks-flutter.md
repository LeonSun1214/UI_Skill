# Flutter (0.18.0, 2026-09-27)

The second part of the second tier. A Flutter app has no DOM, even on the web, where it draws one
canvas. So `render.mjs` had nothing to measure, and the inspector read a Flutter project as "static
HTML", greenfield: compass_app as "static HTML · Bootstrap (local)" because of its web folder.

## The material

| | what | why |
|---|---|---|
| counter | `flutter create`, Flutter 3.47.5 (Dart 3.13) | the smallest app; the seed in the dot shorthand (`.fromSeed`) |
| compass_app | flutter/samples: go_router, provider, MVVM, google_fonts, CachedNetworkImage | a `ColorScheme` pair in its own file, a `TextTheme` with its own grey, `Dimens.of(context)`, a redirect to `/login`, development and staging entry points |
| navigation_and_routing | flutter/samples: go_router with shells, a sign-in form | a redirect that a form satisfies, an adaptive scaffold |
| material_3_demo | flutter/samples: every Material 3 component | 44 tappable nodes, layouts that animate between widths |
| cupertino_gallery | flutter/samples: a `CupertinoApp` | the tab scaffold, San Francisco |
| form_app | flutter/samples: forms | fields, a sign-in form reached by tapping |
| LocalSend | a large app: a Rust core through flutter_rust_bridge, Refena, window_manager, Yaru | what a widget test cannot start |
| one fixture | `flutter-app` (Trailhead) | CI, with six planted defects |

## The renderer

A widget test, written into the project's `.ui-craft/` and run with `flutter test`. It starts the
app through its `main()` and walks to the screen: a route, stored flags, typing, taps, or one screen
pushed over the app. At three widths, in light and dark and at 200 % text, it saves screenshots and
measures the pixels and the semantics tree. A run takes 10–35 seconds on these apps. LocalSend's
test took 43 seconds, after a `flutter pub get` that the script ran itself.

What it found, all real:
- **compass_app, `/search`.** The grey `#A4A4A4` is 2.49:1 on white. It shows in the search hint
  (`search_bar.dart:98`), in "Add Dates" (`search_form_date.dart:65`), in the guest count
  (`search_form_guests.dart:78`), and in the ± icons (`:71`, `:90`).
  - The same ± buttons are 24×24 and have no label (`:66`, `:85`), and so does the 40×40 home
    button (`home_button.dart:39`).
  - The disabled Search button's grey text is counted apart: WCAG exempts it.
  - The inspector had flagged the same grey from the theme alone: "bodySmall #A4A4A4 on surface
    2.5 / 7.6 ✗".
- **compass_app, home.** The logout button is 40×40 with no label
  (`logout_button.dart:51 (InkResponse)`). The dark theme renders, and none of its text fails.
- **compass_app, continent cards.** White names on `#A4A4A4` measure 2.36:1: the card's error
  colour, which shows when its photo fails. Here every photo fails, because the test has no network.
  - The code notes that some of these images fail in production too, so the finding is a real
    state, but one the render reaches only because of the test.
  - The report says why the photos are missing: "7 requests failed (rstr.in ×7) — a widget test
    answers every request with HTTP 400". `--network` sends the requests out. The proxy here
    refuses that host (403), and the report says so.
- **material_3_demo.** 14 tappable nodes have no label at 1440:
  - seven icon buttons without a tooltip (`buttons.dart:25`, `:51`, `component_screen.dart:1244`–`1310`,
    `:1821`) and a FAB (`:1782`);
  - six component cards whose `GestureDetector` only moves focus (`component_screen.dart:2580`).
    They are tappable nodes all the same.
- **cupertino_gallery.** The tab bar's 10px labels fail: "Widgets" `#007AFF` on `#F9F9F9` is
  3.81:1, and "Settings" `#999999` is 2.7:1 (`gallery_home.dart:21 (CupertinoTabScaffold)`).
  These are iOS's own tab-bar colours, which the gallery keeps.
- **LocalSend.** `main()` cannot load the Rust library in a test. The app shows its own error
  screen, and the report says that screen is what it measured, and names the native library.
  - Two plugins have no platform in a test, and the report names their channels:
    `dev.fluttercommunity.plus/package_info` (from `init_error.dart:58`) and `window_manager`
    (from `tray_helper.dart:82`).
  - The next step is `--widget … --standalone` or a `--setup` file.
- **navigation_and_routing and form_app.** Both are clean. The Bookstore renders past its sign-in:
  `--enter Username=… --enter Password=… --tap 'Sign in' --route /authors`. Its scaffold switches
  to a side rail at 1440.
- **The fixture.** All six planted defects were found, each with its file and line and in the
  passes it belongs to:
  - the Row that overflows at 375 (`trips_screen.dart:17`);
  - the fixed-height column that overflows at 200 % text (`trip_card.dart:37`);
  - `bodySmall` #9E9E9E at 2.67:1 (`:41`);
  - the dark scheme's `outline` used for text, 2.11:1 in dark only (`:42`);
  - the unlabeled 28×28 heart (`:49`);
  - the icon button without a tooltip (`trips_screen.dart:25`). At 375 it is off screen, past the
    overflow.

  After a fix, `--compare` located the change (y 128–346). It also showed that the new grey, which
  passes on white, fails on the dark surface (3.02:1): a `TextTheme` colour applies to both
  brightnesses.

Found and fixed on the way:
- **Findings pointed at the scroll view.** The first version named the widget under the node's
  centre by hit-testing. An `InkWell` adds its semantics without a gesture render object, so the
  first gesture handler on the path was the `CustomScrollView`'s. Now the render object that owns
  each semantics node is found (`debugSemantics`), and its creator is named.
- **Flutter's `textContrastGuideline` misses most text.** It checks a node only when its label is
  a single `Text`. On compass_app's home, the list rows merge title and dates into one label, so
  it checked 3 texts. Where it does check, it takes the most common dark and light pixels in the
  box, so anti-aliased edges and dividers count as the text colour: it failed cupertino_gallery's
  black list items at 4.17:1.
  - The contrast numbers now come from a check of every visible run of text and every field. It
    takes the colour the text is set in, composited over the colour most of its box shows. That
    colour must appear in the pixels, or the text is not where it sits (a route over it, a fade).
  - The guideline's result is reported as a count, not as findings.
- **google_fonts failed eleven times per run.** It asks the network, and the test answers 400. The
  script now fetches the faces by the hashes the package lists and caches them. It also puts them
  in the support folder that the path_provider mock points at, so google_fonts loads them itself.
- **One run took 116 seconds.** Each image that could not load waited 3 seconds, once per pass.
  Now all images are awaited together with one limit, and the run takes 30 seconds.
- **A label under a pushed screen was measured** ("Book New Trip", 1.05:1 on the login screen).
  Text is now walked the way semantics walks the tree: onstage only, skipping routes under an opaque
  one, an `Offstage`, and an `Opacity` of 0.
- **Overflows from layout transitions.** Going from 1440 back to 375, material_3_demo animates its
  layout, and the frames in between overflowed 36 times. After the resize settles, the render tree
  is reassembled: a `RenderFlex` reports its overflow once in its life, and this re-arms it. The
  frame that follows reports only the overflows of the settled layout, and there were none.
- **`--widget` imported the wrong file.** `return LoginScreen(` in the router matched as a
  declaration. A top-level declaration now has to start at column 0.
- **`--standalone` crashed on `AppLocalization.of(context)!`.** The app's `localizationsDelegates`
  and `supportedLocales` now come along with its theme.
- **A failed image's error text read as an error screen.** It is left to the network line.
- **The inspector.**
  - `flutter create`'s counter was "established" because of the template's seed; it is now read
    as a template.
  - A `SizedBox(height: 64, child: …)` was counted as spacing.
  - Named steps (`Insets.md`, `Dimens.of(context).paddingScreenHorizontal`) were not counted at all.
  - The dark `outline` used as text was invisible to the static check. `outline` and
    `onSurfaceVariant` on the surface are now measured.

## Checked for regressions

- `inspect.py` on 58 earlier projects and fixtures, markdown and JSON: identical to 0.17.0's
  output. The Flutter code runs only when a pubspec depends on Flutter.
- `render.mjs` is unchanged. Self-test: 38 checks.
- CI: 17 new assertions on the fixture's inspection. A new `flutter` job installs stable Flutter
  and asserts 13 results of two renders; locally, all 13 pass on a fresh copy.

## Not measured yet

No agent has done a task on a Flutter project. Two tasks would show whether the inspector's lines
are read before a colour is typed and whether the render runs without help:
- a match task on compass_app: a new search filter in `Dimens` steps and the theme's colours;
- a fix task on the fixture.

The first of them, the match task, is `trial-flutter-9.md` (0.19.1).

Nothing here runs on a phone: safe areas, the platform's own text-size steps, the order a screen
reader reads in, and frame times are not measured. San Francisco is not available to the test, so
Cupertino text is drawn in Roboto.

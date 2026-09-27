# Flutter

Read when `inspect.py` says the stack is Flutter. What differs from a web project, what `flutter_render.mjs` sees and cannot, and how its findings translate into widgets.

## Where things are

- **Pages are screens, and routes say where they are.** With go_router, `GoRoute(path:, builder:)` builds a screen, a `ShellRoute` or `StatefulShellRoute` wraps the routes under it in the chrome (the `NavigationBar` or `NavigationRail` is in its builder), and `redirect:` is the guard (a sign-in, an onboarding). auto_route marks screens with `@RoutePage()` and generates the router; Navigator 1 apps list named routes in `MaterialApp(routes:)` or `onGenerateRoute`. A route's builder often makes the screen's view model (`LoginScreen(viewModel: LoginViewModel(authRepository: context.read()))`): that is how to build the screen elsewhere. The inspector prints each screen with its paths, the shell it sits in and the redirect in front of it.
- **The look is ThemeData.** A `ColorScheme` (a literal one per brightness, or `ColorScheme.fromSeed` / `colorSchemeSeed`, which Material 3 expands into every role), a `TextTheme`, component themes (`filledButtonTheme`, `inputDecorationTheme`), and `ThemeExtension`s for the app's own tokens. Widgets read `Theme.of(context).colorScheme.primary` and `textTheme.bodyMedium`; a constants class holds the palette (`AppColors`) and the spacing steps (`Insets.md`, `Dimens.paddingHorizontal`). A new widget reads the same: a role, a text style, a step — no `Color(0x…)`, no bare 13.
- **Material or Cupertino.** `MaterialApp` is Material 3 unless `useMaterial3: false`; `CupertinoApp` draws iOS widgets with `CupertinoThemeData`. Many apps mix them (`Switch.adaptive`, a Cupertino date picker in a Material app).
- **Layout by width.** `MediaQuery.sizeOf(context).width` or a `LayoutBuilder` switches layouts: a bottom `NavigationBar` on a phone, a `NavigationRail` from 600 or 840, two panes on a desktop. The renderer's three widths land on each side of those breakpoints.

## Dark mode

- `theme` + `darkTheme` + `themeMode` (`ThemeMode.system` follows the device). The renderer runs the dark passes under a dark platform brightness; `MaterialApp` switches as it would on a phone.
- An app that keeps the user's choice (shared_preferences, Hive) and starts in it: pass the stored value with `--prefs KEY=VALUE` (the inspector prints the keys it found). An app that reads the brightness once at start (into a provider): `--dark-first` starts the whole run dark.
- When the dark pass changes nothing, the report says so and drops it: there is no dark theme.

## Rendering: flutter_render.mjs

- A widget test, run with `flutter test`: it needs the Flutter SDK (on `PATH`, `FLUTTER_ROOT`, or the project's `.fvm/flutter_sdk`) and the packages (`flutter pub get`, run for you the first time). The test is written to `<project>/.ui-craft/render_test.dart` (with a `.gitignore`); a run takes 15–60 seconds.
- It starts the app through its own `main()`. At 375 / 768 / 1440, in light and dark, and at 375 with text at 200 %, it saves a screenshot (2×) and measures: the contrast of every visible run of text and every icon (the colour it is set in over the colour its box shows), tap targets against 48dp (Android) and 44pt (iOS), a label on every tappable node, and each layout overflow of the settled layout. Every finding names the widget in the app's code, with its file and line.
- It also lays the screen out at 360 × 568, a 360 × 640 Android phone below its status and navigation bars, for overflows only (`360x568.png`): a screen that does not scroll runs out of room there first, and 812 hides it. `--viewports 360x640,768,1440` gives a width a height of your own.
- **What a widget test does not have:**
  - *Network*: every request gets HTTP 400, so images from the web show their placeholder or error widget, and data from an API never arrives (a spinner that never settles, an empty list). `--network` lets requests through where the machine can reach the host.
  - *Plugins*: shared_preferences and path_provider are mocked. Any other plugin throws `MissingPluginException`: answer its channel in a `--setup` file (`TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(const MethodChannel('<channel>'), (call) async => null)`), or pump a screen that does not call it.
  - *Native code and services*: an FFI library (a Rust bridge) and Firebase's `initializeApp` fail. The app then shows its error screen, which the report flags as such. Pump the screen itself: `--widget 'X(…)' --standalone`.
  - *San Francisco*: it exists only on Apple platforms, so Cupertino text is drawn in Roboto. Roboto and Material Icons come from the SDK, the app's own fonts from its pubspec, and google_fonts' faces are fetched once and cached (`~/.cache/ui-craft/google-fonts`).
- **Getting to a screen:**
  - `--route /trips/rainier` arrives the way a deep link does, so the router's `redirect` still runs.
  - Behind a sign-in, either set the flag the redirect reads (`--prefs signed_in=true`) or sign in: `--enter Email=a@b.co --enter Password=x --tap 'Sign in'`. Steps run in the order given.
  - `--widget 'SettingsScreen()'` pushes one screen over the running app. `context` is in scope, so `context.read()` finds the app's providers.
  - `--standalone` does not start the app. It pumps the screen in a `MaterialApp` with the app's theme and localizations (when they are plain references). Providers the screen needs go in the expression: `--widget 'ChangeNotifierProvider(create: (_) => Cart(), child: CartScreen())'`.
  - The files that declare the expression's names are imported. For anything else, add `--import`.
- **Generated code** (freezed, json_serializable, auto_route, riverpod_generator): when the `*.g.dart` files are not checked in, run `dart run build_runner build --delete-conflicting-outputs` first. The report says so when the test does not compile for that reason.
- **Not render.mjs.** `flutter run -d chrome` draws the app on a canvas (CanvasKit). A browser audit sees one `<canvas>` and no text, so render.mjs has nothing to measure there.

## The findings in Flutter terms

- **contrast**:
  - Fix the colour where it comes from, for both brightnesses: a `ColorScheme` role, a `TextTheme` style, a literal in the widget.
  - Secondary text reads `colorScheme.onSurfaceVariant`, not a grey literal.
  - A `TextTheme` colour set once applies in dark too: a grey that passes on white can fail on `#121212`.
  - Text in disabled controls is exempt, and counted apart.
- **icon contrast** (3:1): the `Icon`'s `color`, or the `IconTheme` it inherits.
- **unlabeled**:
  - An `IconButton` takes `tooltip:`, which becomes its label.
  - A `GestureDetector` or `InkWell` around an icon has no label and no button role: use an `IconButton`, or wrap it in `Semantics(button: true, label: '…')`.
  - An `Image` takes `semanticLabel`, or `excludeFromSemantics: true` when it is decoration.
- **targets**:
  - Material's minimum is 48×48. `IconButton` meets it, and so do buttons at `MaterialTapTargetSize.padded`.
  - A `GestureDetector` is only as big as its child: make the child 48×48 or use an `IconButton`.
  - `visualDensity: VisualDensity.compact` and `shrinkWrap` take buttons below it.
- **overflow** ("A RenderFlex overflowed by 115 pixels on the right"): a `Row` whose children do not fit.
  - Wrap the text in `Expanded` or `Flexible` (with `overflow: TextOverflow.ellipsis` if one line must stay one line).
  - Use `Wrap` for chips, or switch the layout at a width.
  - At 200 % text, a fixed `height` around text is the usual cause: let the box size to its content, or use `ConstrainedBox(constraints: BoxConstraints(minHeight: …))`.
  - On the small phone, on the bottom: a screen that is a `Column` with no scroll view, and a row added to it. Put the part that grows in `Expanded(child: SingleChildScrollView(child: Column(…)))` and keep the bottom button outside it, or make the screen a `ListView`.
  - Clamping the text scale (`TextScaler.noScaling`, `withClampedTextScaling`) hides the overflow and fails WCAG 1.4.4. The inspector counts those.
- **never settled**: an animation that runs forever. It is usually a progress indicator waiting for data the test does not get.
- **errors**:
  - `MissingPluginException`: a plugin (see above).
  - `Null check operator used on a null value` in a standalone screen: usually a provider or a localization delegate it expects above it.

## Without the SDK: what to check by reading

- The inspector's contrast of the scheme's pairs (`onPrimary` on `primary`, the `TextTheme`'s own colours on `surface`).
- A `tooltip` on every `IconButton`, and `Semantics` on every tappable `GestureDetector` or `InkWell`.
- No fixed heights around text, and no clamped text scale.
- `Expanded` or `Flexible` on text in a `Row`.

## Checks

- `flutter analyze` and `dart format --output=none --set-exit-if-changed .`.
- The project's tests: `flutter test`. A project with golden tests updates them with `--update-goldens`, and only on purpose.
- A widget test of your own draws text in Flutter's test font, each glyph a square as wide as the font size. Text there is wider than in Roboto, so a row wraps or overflows sooner, and sizes measured there are not the app's. Measure layout with the renderer, which loads the real fonts; keep your test to behaviour.

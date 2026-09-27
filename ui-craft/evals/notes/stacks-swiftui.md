# SwiftUI (0.19.0, 2026-09-27)

The last part of the second tier, and the only stack here that is read, not rendered. SwiftUI draws only on
Apple platforms. The skill's renderers run in a browser (`render.mjs`) or a Flutter test
(`flutter_render.mjs`), and this machine has no Mac. So this version is the inspector and the notes. Before
it, both projects below came out as "no package.json or no recognised UI stack", greenfield.

## The material

| | what | why |
|---|---|---|
| Food Truck | apple/sample-food-truck: an iOS and macOS app, iOS 16.4 | a `NavigationSplitView` whose detail column switches on a `Panel` enum, `navigationDestination(for: Panel.self)`, 19 asset colours in three catalogs (app, package, widgets), a `Color` extension, a menu bar scene, 48 previews |
| IceCubes | Dimillian/IceCubesApp: a Mastodon client, iOS 18.5, Swift 6, 13 local packages | a tab enum (`AppTab`), a router enum pushed from a `View` extension (`RouterDestination`, 28 cases), a sheet enum (`SheetDestination`, 24), `navigationDestination(item:)` for settings, windows of their own (`WindowGroup(for:)`), eight theme pairs as types (`IceCubeLight` / `IceCubeDark` …), a 735-key string catalog, accessibility fonts in `UIAppFonts` |
| one fixture | `swiftui-app` (Harbor), an app playground | CI, with five planted issues |

## What the inspector reads now

- **Food Truck.**
  - 19 of 62 views are screens. The root is `ContentView`. The `Panel` switch picks `TruckView`,
    `OrdersView`, `SocialFeedView`, `AccountView` and five more, and the same enum is pushed for four
    of them. Donut editing and orders are pushes, and sign-up, the subscription store and a completed
    order are sheets. Each screen carries its title ("Orders", "Top 5 Donuts") and whether it has a
    preview.
  - The 19 asset colours are listed in light and dark: 13 have a dark variant, and the system
    `AccentColor` (systemIndigo) is labelled as a system colour.
  - One colour is used as text and would fail on the system background (LightIndigo, 1.8:1 on
    white). The line says it assumes that background: the widget draws it in the Dynamic Island,
    which is always black, where it is 11.5:1.
  - `.secondary` is used 29 times. There are 41 text styles against one fixed size, and no
    `.accessibilityLabel` anywhere.
  - Two things need a fix: four `.onTapGesture` calls with no button trait, and one image-only
    button (`SubscriptionStoreView.swift:83`).
  - The verdict is now *established*: the asset catalog, text styles, spacing 10 and radius 16.
- **IceCubes.**
  - 66 of 183 views are screens, ranked so the first 30 are the ones that matter: `AppView`, then
    the tabs `AppTab` picks (Timeline, Notifications, Explore, Messages, Profile …), the eight settings
    screens `SettingsStartingPoint` pushes, then `RouterDestination`'s 28 cases and
    `SheetDestination`'s 24.
  - The status editor and the media viewer also open in windows of their own. Titles are keys in
    the string catalog, and they print as their English text ("Push Notifications").
  - The eight theme pairs print with the contrast of text on each background (label on the Desert
    theme's dark secondary background: 7.8:1).
  - The bundled fonts are Atkinson Hyperlegible and OpenDyslexic, both chosen for accessibility.
  - It sets 55 accessibility labels, 30 hidden elements and 23 traits. Still, 40 buttons have only
    an image as their label and no accessibility label. I checked two: `Image(systemName: "bell")`
    and `"trash"`, both real.
  - It uses `.secondary` 87 times, `.lineLimit(1)` 19 times, and three fixed sizes.
- **The fixture.** All five planted issues are reported:
  - `Muted` #9CA3AF as text: 2.5:1, with no dark variant;
  - the image-only toolbar button (`BerthsView.swift:20`);
  - the `.onTapGesture` on a stack;
  - a `.system(size: 13)` and an Avenir Next at a fixed size;
  - the `.secondary` captions.

  The navigation reads as it is written: three tabs, the `Route` enum's three pushes, and the
  filter sheet.

One line holds for every SwiftUI project, and no rendering is needed to say it. `.secondary` is iOS's
secondaryLabel, `rgba(60, 60, 67, 0.6)`, which composites to #8A8A8E on white: 3.45:1. Body text needs
4.5:1. The inspector says so wherever it counts `.secondary`.

Found and fixed on the way:
- **IceCubes' router is outside every view.** `withAppRouter()` is a `View` extension, so reading
  only view bodies found none of its 28 destinations. Switches that pick a screen are now read in any
  file. Whether a switch is a push, a sheet, a window or a selection comes from the code just before it.
- **A sheet called without a dot was missed.** Inside an extension it is `sheet(item: sheetDestinations)`,
  and the pattern expected `.sheet(`.
- **Closure parameters named the enums.** A switch on `destination` or `targetView` was labelled with
  the closure parameter. The enum is now found through the binding's type in the function's
  parameters (`Binding<SheetDestination?>`) or the property's type (`SettingsStartingPoint`).
- **Extra windows counted as roots.** `WindowGroup(for: WindowDestinationEditor.self)` made the
  editor a second app root; it is now a window of its own.
- **Loading-state switches looked like screen pickers.** `.loading` / `.display` / `.error` picking
  a row or a placeholder is no longer one.
- **Titles printed as keys.** "settings.push.navigation-title" is now resolved through the string catalog.
- **System colours in asset catalogs** (`systemIndigoColor`, `labelColor`) are resolved to iOS's
  light and dark values. They are not marked "no dark", because they adapt on their own.
- **The verdict said greenfield for Food Truck.** The rule knew nothing of asset catalogs or text
  styles.

## Checked for regressions

- `inspect.py` on the 66 earlier projects and fixtures, Flutter's included, markdown and JSON:
  identical to 0.18.0. The SwiftUI code runs only for an Xcode project or Swift package with no
  `package.json` or pubspec beside it; a React Native app's `ios/` project does not count.
- `render.mjs` and `flutter_render.mjs` are unchanged. CI: 20 new assertions on the fixture.

## Not measured

Nothing was rendered.

The Mac loop in `references/stacks/swiftui.md` is the standard one, but it was not run here:
- previews and their variants;
- swift-snapshot-testing at three devices, light, dark and an accessibility text size;
- `performAccessibilityAudit()`;
- `simctl` for appearance and text size.

These are not measured from code:
- contrast on the actual background (the inspector assumes the system background, and says so);
- tap-target sizes;
- truncation at large text sizes;
- VoiceOver's reading order.

A Mac and one agent task (a new settings row in IceCubes' style, say) would show whether the
inspector's lines are what a SwiftUI change needs.

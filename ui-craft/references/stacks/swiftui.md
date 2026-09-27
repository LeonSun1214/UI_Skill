# SwiftUI

Read when `inspect.py` says the stack is SwiftUI (or UIKit). What the inspector reads, what only a Mac can render, and how the findings translate into modifiers.

**Nothing here renders on Linux or Windows.** SwiftUI draws only on Apple platforms. The render loop is a Mac's: Xcode's previews, a snapshot test, or the simulator. The Mac workflow below is the standard one, but ui-craft's scripts do not run it, and it has not been checked by this skill. On any other machine, the review is the inspector's report plus reading.

## Where things are

- **The app** is the `@main` struct that conforms to `App`. Its `WindowGroup { RootView() }` shows the root view. `WindowGroup(for: T.self)` opens a window of its own for a value, `Settings { }` is the macOS settings window, and `MenuBarExtra` is the macOS menu bar item.
- **Screens are views, reached in four ways:**
  - **Tabs**: `TabView { Tab("Home", systemImage:) { HomeView() } }`, or the older `.tabItem { Label(…) }`, or a tab enum whose `makeContentView()` switches on `self`.
  - **Pushes**: `NavigationLink(value:)` plus one `.navigationDestination(for: Route.self) { route in switch route { … } }`. This is often a `View` extension that every stack applies (`.withRoutes()`, IceCubes' `.withAppRouter()`).
  - **Presentation**: `.sheet`, `.fullScreenCover` and `.popover`. With `item:` they often switch on a sheet enum.
  - **Selection**: a `NavigationSplitView` whose detail column switches on the sidebar's selection (Food Truck's `Panel`).

  The inspector prints each screen with its navigation title (resolved through `Localizable.xcstrings`) and how it is reached (`Route.berth (pushed)`, tab "Bookings", a sheet in BerthsView). It also prints each enum that picks screens, case by case.
- **The look.**
  - Asset catalog colours (`Assets.xcassets/*.colorset`), with *Any*, *Dark* and optionally *High Contrast* appearances. Code reads them as `Color("Brand")`, or as the symbol Xcode generates (`Color.brand`, `.brand`).
  - The system's semantic colours: `.primary`, `.secondary`, `Color(.systemBackground)`, `.tint`.
  - Text styles (`.font(.headline)`), which follow Dynamic Type.
  - Sometimes a `Color` extension or a theme type per scheme (IceCubes' `IceCubeLight` / `IceCubeDark`).

  The inspector prints every colour set in light and dark. For each one used as text or tint, it gives the contrast on the system background; for a theme type, the contrast of text on its backgrounds.
- **Packages.** Large apps keep features in local packages (`Packages/Timeline`, `FoodTruckKit`). The screens and assets there count too: the inspector reads the whole tree, including `Package.swift` targets.

## Dark mode

- Semantic colours and asset colours with a *Dark* appearance switch on their own. Literals (`Color(red:…)`, `.white`, `.black`) do not.
- `.preferredColorScheme(.dark)` forces one scheme under it; `UIUserInterfaceStyle` in Info.plist forces it app-wide. The inspector says when either is set.
- `@Environment(\.colorScheme)` branches in code: the inspector counts them.
- An asset colour without a *Dark* variant shows its light value on a dark background. The inspector marks those "(no dark)".

## Rendering on a Mac (not run by ui-craft)

- **Previews.** `#Preview { BerthsView().environment(BerthStore()) }` in Xcode's canvas. Its Variants mode shows light and dark, every Dynamic Type size, and orientations side by side. The inspector counts the views that have a preview.
- **Snapshot tests** with [swift-snapshot-testing](https://github.com/pointfreeco/swift-snapshot-testing), in the app's test target:

  ```swift
  import SnapshotTesting
  import SwiftUI
  import XCTest
  @testable import Harbor

  final class ScreenSnapshots: XCTestCase {
      func testBerths() {
          let view = BerthsView().environment(BerthStore())
          for (name, device) in [("se", ViewImageConfig.iPhoneSe), ("phone", .iPhone13), ("pad", .iPadPro11)] {
              assertSnapshot(of: view, as: .image(layout: .device(config: device)), named: name)
              assertSnapshot(of: view, as: .image(layout: .device(config: device), traits: .init(userInterfaceStyle: .dark)), named: "\(name)-dark")
              assertSnapshot(of: view.environment(\.dynamicTypeSize, .accessibility3), as: .image(layout: .device(config: device)), named: "\(name)-ax3")
          }
      }
  }
  ```

  Run it with `xcodebuild test -scheme <App> -destination 'platform=iOS Simulator,name=iPhone 16'`. The first run records the images, and later runs compare against them. That is `--compare` for SwiftUI.
- **The accessibility audit.** In a UI test on iOS 17 and later, `try XCUIApplication().performAccessibilityAudit()` checks the running screen: contrast, hit regions, clipped text at large sizes, labels, and traits. Xcode's Accessibility Inspector runs the same audit by hand.
- **The simulator by hand:**
  - `xcrun simctl ui booted appearance dark`
  - `xcrun simctl ui booted content_size accessibility-extra-large`
  - `xcrun simctl io booted screenshot shot.png`

## The inspector's findings, in SwiftUI terms

- **`.secondary` text.** It is iOS's secondaryLabel, about 3.5:1 on white: below 4.5:1 for body text, though fine on black (6.3:1). For small text that must be read, use `.primary`, or a custom colour at 4.5:1 or more. Increase Contrast raises secondaryLabel, but only for users who turn it on.
- **An asset colour used as text below 4.5:1.**
  - Darken its *Any* appearance, or keep it for decoration.
  - Give it a *Dark* appearance, and a *High Contrast* one if it carries meaning.
- **A button whose label is only an image.** VoiceOver reads the symbol's name ("line.3.horizontal.decrease.circle") or a guess. Two fixes:
  - `.accessibilityLabel("Filter")`;
  - `Label("Filter", systemImage: …)` with `.labelStyle(.iconOnly)`, which keeps the name for VoiceOver.
- **`.onTapGesture` on a stack or an image.** VoiceOver does not say "button", and Full Keyboard Access cannot reach it. Use a `Button`, or add `.accessibilityAddTraits(.isButton)` and an `.accessibilityAction`.
- **Fixed sizes.** `.font(.system(size: 13))` and `.custom("Avenir Next", size: 17)` without `relativeTo:` stay put when the user raises their text size. Use a text style, `.custom(…, size: 17, relativeTo: .body)`, or `@ScaledMetric` for a number that should scale with text.
- **Text that shrinks or cuts off at large sizes.** `.lineLimit(1)` and `.minimumScaleFactor` cause it: let the text wrap, or switch layouts with `ViewThatFits`.
- **Tap targets.** Apple asks for 44×44 points. An image button is only as big as its image: add `.frame(minWidth: 44, minHeight: 44)` and `.contentShape(Rectangle())`.
- **Motion.** Read `@Environment(\.accessibilityReduceMotion)` and shorten or skip animations. The inspector counts where it is read.

## Checks

- On a Mac: `xcodebuild build` and `xcodebuild test` (the snapshot and UI tests).
- Anywhere: `swift-format` or SwiftLint when the project has a config.

# React Native and Expo

Read when `inspect.py` says the stack is Expo or React Native. What differs from a web project, what the renderer can and cannot see, and how its findings translate into React Native props.

## Where things are

- **Pages are screens.** With Expo Router, a file in `app/` (or `src/app/`) is a route: `(group)` folders do not show in the URL, `[id].tsx` is a parameter, `_layout.tsx` wraps the folder in a `<Stack>`, `<Tabs>` or `<Drawer>`, and a layout that returns `<Redirect href="/sign-in" />` guards everything under it. Route files are often one line (`export { default } from '@/features/feed/feed-screen'`); the inspector follows them to the screen. With React Navigation, screens are `<Stack.Screen name component>` inside a navigator (or `screens: { … }` in the static API), a tab navigator nested in a stack is a screen of that stack, and an auth flow is a ternary: `{signedIn ? <Screen name="Home" /> : <Screen name="SignIn" />}`. The inspector prints each screen with its navigator and the branch it sits in (`shown when !signedIn`).
- **URLs.** Expo Router's routes are URLs. React Navigation has URLs on the web only through `linking` (`config.screens`); without it every screen shows at `/`, and the render reaches another screen by tapping to it (`--act click:text=Settings`). The inspector reads the linking config and prints each screen's path.
- **The look is a theme object, not a stylesheet.** Most apps keep a colour map per scheme (`Colors.light` / `Colors.dark` in `constants/theme.ts`, or `colors.ts` beside `colorsDark.ts`), a spacing scale, and fonts; components read them through a hook (`useTheme()`, `useAppTheme()`) and style with `StyleSheet.create` or typed style objects. The inspector prints the map with both schemes side by side and the contrast of its text colours on its background. A new component takes the same route: the hook, the theme's names, the spacing scale — no hex values, no bare numbers where the scale has a step.
- **Kits.** React Native Paper (`<PaperProvider theme>`, Material 3: `MD3LightTheme` spread and overridden), NativeWind or Uniwind (Tailwind classes on `className`; the tokens are in `tailwind.config.js` or a `global.css` `@theme`, and the Tailwind counts apply), Tamagui (`tamagui.config.ts`, `$tokens`), gluestack-ui (NativeWind underneath). React Navigation's own theme (`DefaultTheme` / `DarkTheme`, spread with overrides) colours headers and tab bars. The inspector fills in what a spread theme leaves at its defaults, so the pairs it prints are what the app shows.
- **Platform files.** `card.web.tsx` beside `card.tsx` replaces it in the browser; `.ios.tsx` / `.android.tsx` on each phone. The inspector lists the web twins: a fix made in one is not made in the other. `Platform.OS === 'web'` branches differ the same way.

## Dark mode

- Almost every app follows the device: `useColorScheme()` picks `Colors[scheme]`. Many also keep a user's choice (MMKV, AsyncStorage) that overrides the device; the inspector names the key. `userInterfaceStyle` in `app.json` (`light`, `dark`, `automatic`) fixes the native build's scheme whatever the code does — on the web it has no effect.
- react-native-web reads the scheme through `matchMedia`, so there are no dark CSS rules to find. The renderer tries a dark device on every react-native-web page: when the page's colour moves, it measures the dark pass (`rendered (device scheme)`); when nothing moves, it says the app has no dark mode or keeps its own choice. NativeWind and Uniwind write real CSS on the web (a `.dark` rule or a `prefers-color-scheme` query), and the pass finds it as on any web page.
- To render the app's own stored choice: `--dark-storage 'mmkv.default\KEY=dark'` (MMKV) or `--dark-storage KEY=dark` (AsyncStorage), with the key the inspector prints.

## Serving and rendering

- `npx expo start --web` (usually the `web` script) serves the app through react-native-web on :8081 (`--port 8082` for a second app). The first request bundles the app, which takes 20–60 seconds on a cold server; the render retries a load that times out once. Stop the server by its port's process group when done.
- Without `react-native-web` in the dependencies (a bare React Native CLI app) there is no web build, and the renderer cannot show the app. `npx expo install react-native-web react-dom @expo/metro-runtime` adds it to an Expo app; a bare app needs Expo's web support or its own webpack setup. Otherwise review statically with the rules below, and check on a simulator.
- Native-only modules (`react-native-maps`, `react-native-vision-camera`, `react-native-webview`, Nitro modules) have no web version: a screen that uses them fails or renders empty in the browser. The inspector lists them.
- **Storage on the web.** AsyncStorage is `localStorage` under the same key. MMKV is `localStorage` under `mmkv.default\KEY` (or `ID\KEY` for `createMMKV({ id })`); SecureStore does not exist on the web. So a screen behind sign-in or onboarding renders with the state in place: `--storage 'mmkv.default\auth.token=demo'`, `--storage 'mmkv.default\IS_FIRST_TIME=false'`. `--storage` sets the key before the app's scripts run and leaves it alone once the app writes it. The inspector prints the keys it found and the flag for the session key.
- The page scrolls inside a ScrollView, not the window. The render scrolls that view to mount lazy content, and takes the full screenshot with the viewport grown to fit it.
- What the render cannot see: the native tab bar (`NativeTabs`) and native headers (the web draws its own), safe-area insets (zero in a browser: the notch and home indicator take space on a phone), `hitSlop` (the phone's touch area is larger than the measured box; the web ignores it), the user's font size (Dynamic Type, Android font scale), and platform-specific files other than `.web`.

## The render's findings, in React Native terms

- **no role** — a `Pressable` or `Touchable*` without `role="button"` (or `accessibilityRole="button"`). react-native-web renders it as a focusable `<div>`; VoiceOver and TalkBack do not say "button" either. With the role, react-native-web renders a real `<button>`.
- **unnamed control** — a `TextInput` whose visible label is a separate `Text`: give it `accessibilityLabel` (read on both phones, `aria-label` on the web); `aria-labelledby` pointing at the label's `nativeID` works on Android and the web, not on iOS. An icon-only `Pressable` needs `accessibilityLabel`.
- **no h1 / headings** — `role="heading"` on the screen's title `Text` (react-native-web renders `<h1>`; `aria-level={2}` makes `<h2>`). Screen readers on the phone use the same role to jump between headings.
- **img without alt** — `alt` on `Image` or expo-image's `Image` (it becomes the accessibility label on the phone), or `accessible={false}` for decoration.
- **no title** — Expo Router: `<Stack.Screen options={{ title: 'Orders' }} />` in the screen or its layout, or `<Head>` from `expo-router/head`; React Navigation sets `document.title` from the screen's `title` option.
- **focus** — react-native-web keeps the browser's focus ring unless a style removes it (`outlineStyle: 'none'`); a ring drawn with a `focused` style must reach 3:1. A closed drawer or an off-screen panel whose items stay in the tab order is reported as focus obscured: hide it from the tab order when closed (`inert`, or `display: 'none'`).
- **targets 24–44px** — iOS asks for 44pt, Android for 48dp. Enlarge the pressable (padding, `minHeight`), not only `hitSlop`: the web ignores `hitSlop`, and a larger box also helps motor-impaired users on the phone.
- **no hover feedback** — the web only. `Pressable`'s `style={({ hovered, pressed }) => …}` receives `hovered` in react-native-web.
- **animations without prefers-reduced-motion** — the render loads the page once more under reduced motion and drops the warning when the animations stop there: Reanimated's animations follow the device setting unless told otherwise (`reduceMotion: ReduceMotion.System`). React Native's own `Animated` does not: read `AccessibilityInfo.isReduceMotionEnabled()` (or Reanimated's `useReducedMotion()`) and skip or shorten the animation.
- **contrast** — fix it in the theme map, for both schemes: the inspector's `text on background` line shows each pair, with ✗ below 4.5:1.

## Without a web build: what to check by reading

Contrast of the theme's pairs (the inspector computes them), a role and a label on every pressable, `accessibilityLabel` on icon-only buttons and inputs, `role="heading"` on screen titles, touch targets of 44pt / 48dp, no `allowFontScaling={false}` on body text (the inspector counts them), and layouts that survive a larger font (no fixed heights on text containers).

## Checks

`npx tsc --noEmit`, `npx expo lint` (or the project's eslint; `eslint-plugin-react-native-a11y` covers roles and labels), and `npx expo-doctor` for dependency versions. The tests, if any: `npx jest`.

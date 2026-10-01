# React Native and Expo (0.17.0, 2026-09-27)

The first part of the second tier. A React Native app has no stylesheet and no HTML: its pages
are screens in navigators or files in `app/`, its look is a theme object and `StyleSheet`, and
it reaches a browser only through react-native-web. The inspector read these apps as plain
React, and the renderer had never seen react-native-web's DOM.

## The material

| | what | why |
|---|---|---|
| Expo template | `create-expo-app` default, Expo SDK 57, Expo Router in `src/app/` | `Colors.light` / `Colors.dark`, `NativeTabs` with a `.web.tsx` twin, a CSS Module the web twin uses |
| Ignite | `infinitered/ignite` boilerplate, Expo 55, React Navigation 7 | an auth ternary in the stack, tabs in their own file, a linking config, `colors.ts` beside `colorsDark.ts` over a palette, the theme choice and the session in MMKV, themed style functions |
| Obytes | `obytes/react-native-template-obytes`, Expo 54, Expo Router, Uniwind | route files that re-export feature screens, a layout that redirects to onboarding and sign-in, Tailwind 4 `@theme`, React Navigation themes spread and overridden, MMKV v4 |
| React Native Paper example | `callstack/react-native-paper/example`, Expo 56 | React Navigation's static API (`createXScreen`), Paper's components, themes built only from Paper's and React Navigation's |
| Bluesky | `bluesky-social/social-app`, Expo 57 | five tab stacks in one file, a `commonScreens(Stack)` function shared by six navigators, `getComponent`, URLs from its own `new Router({…})`, a tsconfig with a block comment |
| two fixtures | `expo-app`, `rn-nav-app` | CI |

Rendered on Expo Web (`npx expo start --web`): the template, Ignite and Obytes. The Paper example
installs from its monorepo root and Bluesky is large; both were inspected, not rendered.

## The inspector, before and after

Before: the Expo template was "React 19.2.3" with no pages. Ignite had 22 pages, every file under
`app/screens/` (its demo components included), because of the folder's name. Obytes had one page
and Tailwind. The Paper example was "static HTML", greenfield. Bluesky had no pages and "UI: Radix
primitives".

Now the stack line reads "Expo ~57.0.25 (Expo Router, file routes in src/app/) · React Native
0.86.3 · react-native-web ~0.21.0". Ignite's six screens come from its navigators, each with its
URL from the linking config and the branch it sits in: `Login` at `/`, "shown when
`!isAuthenticated`", the four demo tabs "inside Tab (tabs) in Stack (stack) as `Demo`". Obytes'
eight routes follow their one-line route files to the feature screens, behind "a redirect to
`/onboarding` when `isFirstTime`, a redirect to `/login` when `status === 'signOut'`". Bluesky's
screens resolve through `getComponent` and the shared function, with URLs from its route table
(`Search` at `/search`, `Lists` at `/lists`). The Paper example's `ExampleList` is at `/`, and its
two themes say they have no colours of their own: Paper's `LightTheme` plus React Navigation's.

Each report has the theme with both schemes side by side and the contrast of its text colours:
the template's `textSecondary` 5.9 / 10.1, Ignite's `textDim` 7.3 / 8.4, Obytes' navigation
themes with React Navigation's defaults filled in where the spread leaves them. The spacing
scale, `StyleSheet` numbers (Ignite: `spacing.md` ×29, radius 25 dominant), fonts (Ignite's
`useFonts` in two entry files, `@expo-google-fonts/space-grotesk`), the web twins, and the keys
each app keeps on the device with their names in a browser: `mmkv.default\ignite.themeScheme`,
`mmkv.default\AuthProvider.authToken`, Obytes' `mmkv.default\IS_FIRST_TIME`.

Found and fixed on the way:
- `_no_comments` removed from the `/*` in `"#/*": ["./src/*"]` to the end of a later block
  comment. Bluesky's tsconfig lost its `paths`, and no `#/` import resolved. Strings are kept
  whole now. On the 48 older projects nothing changed.
- The kit lines' components by use came from a `set`, so ties came out in a different order
  from run to run (Python's hash seed). They are sorted before counting.
- An Expo Router route called `onboarding` was read as a web splash screen ("covers the first
  paint"). The splash heuristic is off for React Native: a redirect to it is a guard, and says so.

## What rendering showed

- **A Pressable without a role is invisible to a web audit.** react-native-web renders it as
  `<div tabindex="0">` with a pointer cursor, and matches none of the selectors for controls. On
  the template's Explore screen the Tab walk measured 1 of 9 tab stops ("1/1 tabbed"); five
  collapsible headers, 24px tall, were outside the target, name and hover checks. A focusable
  element with a pointer cursor now counts as a control, and one without a role is reported as
  `no role`: 9/9 tabbed, 5 without a role, 8 targets between 24 and 44px.
- **Dark mode is in JS.** Every app switches through `useColorScheme()`; there is no dark CSS
  rule, so no dark pass ran. The colours are on a view, and `<body>` stays transparent, so a
  pass would have read "unchanged" anyway. A react-native-web page now gets a pass under a dark
  device scheme, and its colour is read from the outermost view that covers the viewport: the
  template goes white → black and Ignite `#F4F2F1` → `#191015`, with no dark failures on either
  first screen. A page that does not move is dropped from the report, with a line saying the
  pass was tried. Obytes' Uniwind writes a real `.dark` rule, found as on the web.
- **The page scrolls inside a view.** The document is one viewport tall; the ScrollView scrolls.
  The full screenshot was the fold again. It is now taken with the viewport grown to the view's
  content (Ignite's showroom: 12,000px, the cap).
- **Signed in through the app's storage.** `--storage 'mmkv.default\AuthProvider.authToken=…'`
  rendered Ignite's showroom behind its sign-in, and `--storage 'mmkv.default\IS_FIRST_TIME=false'`
  rendered Obytes' sign-in instead of its onboarding.
- **What the renders found, all real:**
  - The template's header pill overflows at 375 (380px). Its three expo-image images have no
    `alt`, and it has no heading role and no title.
  - Ignite's sign-in inputs have no accessible name: the "Email" label is a sibling `Text`. Its
    password toggle is 20px wide and unnamed. Its TextField wrapper is a role-less tab stop.
  - In Ignite's dark theme, `error` stays `#C03403`, 3.73:1 on black, and disabled text is
    1.81:1.
  - Ignite's closed drawer keeps its 30 demo links first in the tab order, behind the content.
    The cover is named by what it holds ("behind the view holding "Components to jump start
    you…""), not by react-native-web's atomic class, and not by a container that holds the
    focused link too.
  - Obytes' input borders are `#D4D4D4`, 1.48:1 (dark: 1.81:1). Its "Login" button has no role.
- **Motion honoured in JS.** The template's logo runs three Reanimated entering animations, which
  are CSS animations on the web, and no stylesheet has a reduced-motion rule: "animations without
  prefers-reduced-motion". Loaded with reduced motion emulated, none of them runs (3 → 0):
  Reanimated reads the setting in JS. A page that animates without the rule is now loaded once
  more under reduced motion, and the warning is dropped when its animations stop there.
- **Font and console noise.** The fonts line said "used: Times New Roman": `<body>`'s default, which
  no text uses when every text node sits in a styled view. It now names the faces the text is set
  in (`-apple-system`, react-native-web's system stack). Material Symbols was measured mid-load;
  the audit waits for `document.fonts.ready`. Reactotron's socket (:9090) failing is a dev tool,
  not the app.

## Checked for regressions

- `inspect.py` on 48 earlier projects and fixtures (every stack so far): the markdown is the same
  except the order of tied counts in nine kit lines (now alphabetical). The JSON gains three keys.
- `render.mjs` on Sunnote `/` and `/new`, TailAdmin Vue `/signin` and `/`, the review and
  established fixtures, and Berry's dashboard (the Vuetify dark pass that moves nothing): the
  same findings, ApexCharts' random element id aside.
- Self-test: 38 checks (a react-native-web page with and without a dark mode). CI: 31 assertions
  on two fixtures.

## Not measured yet

No agent has done a task on a React Native project. A match task on Ignite (a new demo screen in
the showroom's style) or Obytes (a settings row in Uniwind classes) would show whether the theme
lines are read before a colour is typed. (Done in 0.19.2: `trial-rn-10.md`, a checkbox on Ignite's
login screen. The theme lines were read first: the agent ran `contrast.py` on the dark palette
before it wrote code.) Nothing here runs on a phone: native tab bars, safe
areas, `hitSlop` and Dynamic Type are described in the stack notes, not measured.

# Tenth trial — a "Remember me" checkbox on an Ignite app (run 2026-09-27, graded 2026-10-01)

0.17.0 taught the skill React Native: the inspector, `references/stacks/react-native.md`, and a
renderer that reads react-native-web's DOM. They were checked on templates and two fixtures, but
never by an agent doing a task. This trial gives a fresh agent a match task on an app made by
Ignite's CLI (`ignite new`, 11.5.0): Expo 55, React Native 0.83, React Navigation 7,
react-native-web, a theme in `colors.ts` beside `colorsDark.ts`, MMKV. The task, as given:

在登录页的密码框下面加一个「记住我」勾选框：默认不勾，点一下勾上，再点一次取消。风格跟这个表单保持一致，
手机和平板上都要正常，深色模式也要正常，别自己发挥。勾选的值先存在登录页的 state 里就行，不用真的实现记住登录。

The harness was the ninth trial's: a subagent, the skill path, the task verbatim, a clean copy on a
branch of its own, `npx expo start --web` started by the agent, the project's own checks
(`npm run compile`, `npm run lint:check`, `npm test`), no questions. One run, with ui-craft 0.19.1.

The CLI could not finish here: its `npx expo install --fix` is refused by the sandbox's proxy. Its
last steps (`remove-demo-markup`, lint) were run by hand. One type error in the boilerplate,
`navigationUtilities.ts:71` (React Navigation 7.22's `getRootState()` may return undefined), was
guarded in the baseline commit so that `npm run compile` passes. On the clean copy: compile and lint
clean, 4 suites and 20 tests pass.

## What it made

- **The row,** in `LoginScreen.tsx`: the project's own `Checkbox` (`components/Toggle`), the one
  the Showroom uses, with `useState(false)` and `labelTx="loginScreen:rememberMe"`. The row is
  padded `spacing.sm` above and below, so it is 48 px tall around a 24 px box. The password field's
  bottom margin went from `spacing.lg` to `spacing.sm`, so the gaps a person sees stay as they
  were. In dark mode only, the tick is drawn in `colors.background`.
- **Seven dictionaries:** `loginScreen.rememberMe` in `en`, `ar`, `es`, `fr`, `hi`, `ja` and
  `ko`. The dictionaries are typed from `en`, so all seven must have it. The agent translated six
  and said to have them checked.
- **A test:** unchecked at start, one press checks, a second unchecks. It mocks `react-native`
  in that file alone, because `test/setup.ts` replaces `Image` with an object that cannot render,
  and the screen draws icons. Re-run here: compile and lint clean, 5 suites and 21 tests pass.
  With the default flipped to `true`, the test fails (checked).

Graded by rendering the login page again, against a baseline rendered from the pristine copy:

- **Only the row changed.** At 375 the changed pixels are at y 430–600: the row, and the button
  it moved down. Nothing above it moved.
- **No finding of its own.** The baseline's findings are the page's after the change: three
  unnamed controls (the two inputs and the password eye), three clickable elements without a
  role (the two field wrappers and the eye), one target below 24 px (the eye, 20 × 40) and two
  between 24 and 44 (the inputs, 24 px tall). Six texts measured, none below threshold, in light
  and dark.
- **The row** has `role="checkbox"`, is a tab stop with a visible ring (7 of 7 against the
  baseline's 6 of 6), and measures 327 × 48 at 375 and 720 × 48 at 768.
- **Checked** (the agent rendered it with `--act 'click:role=checkbox[name="Remember me"]'`):
  in light, a `#41476E` fill with the component's `#FFEED4` tick, 7.84:1; in dark, `#DCDDE9` with
  the agent's `#191015` tick, 13.82:1. The component's own dark tick, `#FFBB50`, is 1.25:1 on
  that fill. That is real, and every checkbox in the Showroom has it in dark mode.

The decisions it stated in its reply: the padding that makes the row 48 px; the dark-only tick,
with the one-line change that would fix the component for the whole app; the translations; the
mock kept to its own test file. It skipped the critique on purpose: one control, the project's
component, 别自己发挥.

## The reading list, followed

| call | what |
|---|---|
| 1 | SKILL.md |
| 2 | `inspect.py` |
| 3 | `references/stacks/react-native.md` |
| 4–13 | `LoginScreen.tsx`, `Checkbox` and `Toggle`, the i18n files, the two palettes, `contrast.py` on six pairs from them, the theme's types and context, the jest config and the package scripts, `Screen.tsx` and the test setup: about 12 files in 10 calls |
| 14–17 | four edits, refused: the file had been `cat`-ed, not read with the Read tool |
| 18–19 | `expo start --web`, waited for |
| 20 | first render: the login page, as the baseline, before any edit |
| 21–25 | the file read, then the same four edits |

Nineteen calls before the first look, against eight in the two trials before. Ten of them were
project files; four were the refused edits. Call 9 answers the question 0.17.0's notes left open,
whether the theme lines are read before a colour is typed: it ran `contrast.py` on the dark
palette before it wrote any code, and that is where it found the tick at 1.25:1.

## What it cost, and where

| | trial 8 (Nuxt) | trial 9 (Flutter) | trial 10 (React Native) |
|---|---|---|---|
| tool calls | 49 | 45 | 48 |
| tool calls before the first render | 8 | 8 | 19 |
| renders / with `--compare` | 5 / 2 | 2 / 1 | 3 / 2 |
| tokens (billed) · output | 204k · 30k | 203k · 12k | 174k · 8.5k |
| wall clock | 17 min | 17 min | 13 min |

Where the 13 minutes went:
- 4 min of reading, the palette check included;
- 1 min on the refused edits and the server, then the baseline render;
- the edits went in within 10 s, the dictionaries through one python one-liner;
- the test took three calls (write, one fix, pass);
- `verify.py` twice: once as the skill says, once more to filter its 34 FAILs (below);
- the render with `--compare`, the two contact sheets, the checked render;
- the three checks, the default flipped and restored to prove the test, the server stopped by
  its process group (two calls), the copy of the outputs.

## What the trial found in the skill

**`verify.py` reported 34 missing packages.** Every one was an image under `@assets/…`, an
alias in the app's tsconfig. The agent spent a call filtering them and a paragraph of its reply
explaining them. `verify.py` now reads the `paths` of a tsconfig or jsconfig, and a babel
module-resolver's `alias`, and treats an import under one as a path into the project. The first
version of that read the file with the JavaScript comment stripper, which took the `/*` in
`"@/*"` for a comment that ended at the `*/` in `"**/*.ts"`, and found no aliases at all; the
config is now read with its strings kept whole. The app: "148 imports across 33 packages, 0
missing". On the 27 fixtures and three earlier projects, one line changes: the Angular fixture's
`@app/*` alias was a missing package and is not.

**A render audited an empty page.** The first grading render here, on a server whose first web
bundle Metro was still building, measured the 768 viewport as a page titled "IgniteTrial" with no
text and no controls, and passed it; its screenshot, taken later, shows the login page with the
checkbox. The page's `load` event does not wait for the bundle. The report's own line caught it
("at 768 the page was "IgniteTrial", not the one above"), and the agent's three renders were not
affected: its first came 19 s after the server started. The render now waits, after `load`, up
to 20 s for text or a control before it measures, and says when it waited more than 1.5 s.
Checked with Metro's cache cleared (the bundle took 24.6 s): the 1440 viewport waited 1.5 s, the
warning says so, and the three viewports measured the page, identical to the warm run.

**The checkbox has no state on the web.** It has the role, a name, a focus ring and 48 px, and
the audit had nothing to say about it. It has no `aria-checked`, checked or not: react-native-web
0.21 renders a Pressable's `accessibilityRole` and drops its `accessibilityState`, which is all
Ignite's `Toggle` sets. A screen reader in a browser reads "Remember me, checkbox" and never
whether it is on. On the phone the state is there, which is what the agent's test asserts. The
render now reports a `checkbox`, `switch` or `radio` role with no `aria-checked` as "toggles
without state", with the fix: `aria-checked={value}`, which React Native 0.71 and later map to
`accessibilityState` on the phone. On this page: 1.

**Four refused edits.** The eighth trial lost two calls to the same thing. SKILL.md now says to
read a file with the Read tool before editing it.

## On a Mac

The web render cannot show the safe areas, the native dark mode or the system text size. The
user has Xcode; `mac-check.sh` (in `ui-craft-workspace/trial-10/mac/`, not in the repository)
builds the app in the iOS simulator and takes five screenshots: light, checked, dark, dark at
accessibility-large text, and the same after a fresh start. What they show goes here when they
come back.

## Not answered

- One run, one configuration, as in the ninth trial.
- Whether Ignite's `Switch` and `Radio` lack the state on the web too. They share the `Toggle`,
  so they should; neither was rendered here.
- The six translations.
- Everything the phone does: the Mac check above.

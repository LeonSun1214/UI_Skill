# Ninth trial — a budget filter on compass_app (2026-09-27)

0.18.0 taught the skill Flutter: the inspector, `references/stacks/flutter.md`, and a renderer
that runs a widget test. They were checked on samples and a fixture, but never by an agent doing
a task. This trial gives a fresh agent a match task on compass_app, from flutter/samples. The app
uses go_router, provider and MVVM, with a `Dimens` class, a `ColorScheme` pair and its own greys.
The task, as given:

在搜索页（/search）的「When」和「Who」下面加一行「预算」筛选：三个选项 $、$$、$$$，可以选一个，
也可以不选，再点一次就取消。风格跟 When、Who 两行保持一致，手机和平板上都要正常，深色模式也要正常，
别自己发挥。选中的值先存在搜索页的 view model 里就行，不用接到搜索结果。

The harness was the eighth trial's: a subagent, the skill path, the task verbatim, and a clean
copy on a branch of its own. It also had the Flutter SDK's path and the project's own checks,
`flutter analyze` and `flutter test`; on the clean copy analyze was clean and 67 tests passed. No
questions allowed. One run, with ui-craft 0.19.0.

## What it made

- **The new row,** in `search_form_budget.dart`. Its frame copies the When and Who rows: the same
  padding, 64 high, the `grey1` border, radius 16, and the label in `titleMedium`.
  - The options are three `ChoiceChip`s in the states of the app's own `CustomCheckbox`: a `grey3`
    outline when off, filled with `primary` when on.
  - An `OverflowBar` moves them under the label when they do not fit beside it, at 200 % text or
    on a 320 phone.
- **The view model:** `enum Budget { low, medium, high }` and a nullable `selectedBudget`. It is
  not part of `valid` and is not saved into the `ItineraryConfig`, because the task said to keep it
  in the view model.
- **The label:** `budget: 'Budget'` in `AppLocalization`. The app is English only, and "When" goes
  through the same class. The agent said so, and said that 「预算」 is a one-line change.
- **The screen.** It was a `Column` with a `Spacer`, and with a fourth row it no longer fitted a
  small phone. Everything between the search bar and the Search button now sits in
  `Expanded(SingleChildScrollView(Column(…)))`.
- **Three tests:** select, change and deselect; the view model's setter; and the screen on a
  360 × 568 surface, with the Search button still hittable. Re-run here: `flutter analyze` clean,
  70 tests pass, `dart format` clean.

It was graded by rendering `/search` again, against a baseline rendered from a pristine copy.

- **Only the new row changed.** At 375 the changed pixels are at y 462–506 (452–516 in dark,
  where the border shows). At 200 % text the chips wrap under the label (y 472–594). The Search
  button did not move: at 812 the scroll view changes nothing.
- **No finding of its own.** The baseline has the same 10 texts below threshold, 3 unlabeled
  controls and 3 small targets, all older than the change:
  - the `#A4A4A4` hint grey at 2.49:1, in "Search destination", "Add Dates" and "0";
  - the continent names on the grey photo placeholder;
  - the 24 × 24 ± buttons and the 40 × 40 home button.

  The page has 14 tappable nodes against the baseline's 11: the three chips, each 48 high.
- **The selected state** (`--tap '$$'`): a black chip with `#FFF7FA` text, and the reverse in dark.

The decisions it stated in its reply:
- the English label;
- the chip look, taken from `CustomCheckbox`;
- the scroll view;
- the budget resets on leaving `/search`, because the view model is rebuilt on each visit. The
  other three fields come back from the `ItineraryConfig`.

It named the failures the page already had and proposed fixes: `grey2` for the light hint
(8.45:1), and `IconButton`s with tooltips for ± and home. It did not make them, as the task said.

The renderer does not judge one thing here: a screen reader reads the chips as "$", "$$" and
"$$$", with the selected state that `ChoiceChip` gives. Nobody asked for labels such as
"Low budget".

## The reading list, followed

| call | what |
|---|---|
| 1–2 | SKILL.md |
| 3 | `inspect.py` |
| 4 | `references/stacks/flutter.md` |
| 5–8 | 18 project files, four calls: the search form's widgets and view model; the localization, theme, `Dimens` and colours; `CustomCheckbox`; the search form's six tests |
| 9 | first render: `/search`, as the baseline, before any edit |

Eight calls before the first look, as in the seventh and eighth trials. It read 18 project files
against the eighth trial's 9, in four calls.

## What it cost, and where

| | trial 7 (Next.js) | trial 8 (Nuxt) | trial 9 (Flutter) |
|---|---|---|---|
| tool calls | 39 | 49 | 45 |
| tool calls before the first render | 8 | 8 | 8 |
| renders / with `--compare` | 7 / 3 | 5 / 2 | 2 / 1 |
| tokens (billed) · output | 133k · 8.7k | 204k · 30k | 203k · 12k |
| wall clock | 10–11 min | 17 min | 17 min |

Where the 17 minutes went:
- 1.3 min of reading, then the first render (42 s).
- 9 min from the first look to the first edit. There were two more reads (the tag chip and the
  search bar; the test harness and the router) and two long turns of thinking. The design was
  settled there, scroll view included: the edits that followed all went in within 35 s.
- 1 min for the edits, `verify.py` and `flutter analyze`, then the second render (45 s), with
  `--tap '$$'` and `--compare`.
- 4.5 min for the two gaps below, the tests, the format check and the report.

That is two renders, against 7 in the seventh trial and 5 in the eighth. Each render took 30 to
45 s, and the agent used one as the before and one as the after.

## What the trial found in the skill

**The renderer skipped the options' text.** After the second render the agent searched
`report.json` for "$", "$$" and "$$$". It found none, and measured them with `contrast.py`
instead: 19.03:1 unselected, 18.06:1 selected.
- The renderer's per-text check skipped any text with no letter or digit. That rule was meant for
  emoji and punctuation, and a price is neither.
- A currency or maths sign now counts as text. On the trial's page, 13 runs of text become 16, and
  none of the three fails.
- On the ten renders behind 0.18.0's notes nothing else changed: none of them has such text.

**The renderer had no small phone.** It drew phones only at 375 × 812, where a fourth row fits.
- The agent reasoned that the row might not fit on a smaller phone, and made the form scroll.
- It proved the need with a widget test at 360 × 568 (a 360 × 640 Android phone below its bars).
  The test fails when the scroll view is taken out.

The renderer now also lays every screen out at 360 × 568, for overflows only, and saves a
screenshot:
- without the scroll view: "overflow: by 48 px on the bottom —
  lib/ui/search_form/widgets/search_form_screen.dart:37 (Column) · at 360x568";
- the agent's version and the pristine app: no overflow;
- the ten earlier renders: no overflow beyond what they already had at 375.

The agent's test put the overflow at 83 px, not 48. A widget test draws text in Flutter's test
font, where each glyph is a square as wide as the font size, so text there is wider than in
Roboto. The test still answers its own question (does the screen fit), but its number is not the
app's. `flutter.md` now says to measure layout with the renderer, which loads the real fonts.
`--viewports` also takes `WxH` now (`360x640,768,1440`).

**`verify.py` had nothing to read.** On a Dart project it printed "0 imports across 0 packages,
0 missing · 0 icon names checked · 0 web fonts checked". That was true but useless, and the agent
pasted it into its report with a note that `flutter analyze` checks the imports. On a Dart or
Swift project, `verify.py` now says it has nothing to check and names the tool that does.

The fixture's trip page now plants both new cases: a column that overflows only on the small
phone, and a `$$` in `bodySmall`'s grey (2.67:1). CI's `flutter` job checks for both.

## Not answered

- **One run, one configuration.** The ui-ux-pro-max and no-skill runs of the earlier trials were
  not repeated here.
- **Whether the scroll view counts as 自己发挥.** The task said phones must work. The agent
  checked the overflow before it changed the screen's structure, and the change is invisible at
  812. Still, it changes a screen the task did not name; the reply says so.
- **The small phone's height.** 568 is what a 360 × 640 phone leaves below its status and
  navigation bars, which is also what a `SafeArea` or an `AppBar` leaves. A screen that draws
  under the status bar gets 24 px more on the device.
- **How a screen reader words "$$".**

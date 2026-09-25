# Third real-repository trial — Sunnote, a match task run by a fresh agent (2026-09-25)

Sunnote: Vite + React 19 + react-router 7 + Tailwind 3, no backend (state in
`localStorage` under `sunnote:data`), class-based dark mode, a PWA on GitHub Pages.
Task, as a user would put it: 加一个「考试计划」页（/plan），托福和雅思各自的考试日期和目标分，
存进现有的设置数据，仪表盘顶部显示倒计时，导航里加入口，风格跟设置页一致。

Unlike the first two trials this one was run by a fresh agent following SKILL.md
0.9.0 on its own, so its transcript can be measured. Result: page, data model with
normalisation in `migrate`, dashboard countdown card, two nav entries, 14 unit
tests; `typecheck` and 110/110 tests clean; matches the settings page to the
class. 15 minutes wall clock. Pushed as `claude/exam-plan-page`.

| | trial 1 (me, no reading list) | trial 3 (agent, with it) |
|---|---|---|
| read commands before the first render | 29 | 9 |
| tool calls before the first render | 38 | 16 |
| wall clock | ~70 min (two pages, four renders, two critiques) | 15 min (one page + a card, two renders) |
| tokens | not separable from the session | 381k (312k context growth, 68k output) |

Different tasks, so a lean, not a proof: trial 1 also built a cover page. But the
nine reads were the ones the task needs — the types file, the settings page (the
named sibling), the store, the dashboard, the shell, the exam config — and none was
spent finding out what the CSS classes mean or where the strings live. Two of the
reads were multi-file `cat` batches of ~47k characters each; that is where most of
the 312k context growth came from, and it is the reading a feature that touches
the store and the dashboard cannot skip.

What worked for the first time on a real app:

- **`--init-script` seeding from the reading list's storage key.** The dashboard
  only shows the countdown when a date is set; the agent seeded `sunnote:data`
  and rendered a populated dashboard without being told how.
- **Class-based dark mode** (`mode: class`), the third theme mechanism after
  media and attribute.
- **Inherited failures, correctly filed.** The dashboard carries 13 pre-existing
  contrast failures and 5 small targets; the report listed them, the agent
  attributed every one to shell or primitives, kept the settings page's 38 px
  controls for consistency, and gave the one-line `.input` border fix measured
  with `contrast.py`. The only out-of-ask change — two 20 px header icon links
  to 44 px — was disclosed.

What to change:

1. **The Verified block cited a scratchpad path** (`/tmp/…/scratchpad/.ui-craft/plan-1`)
   because the rules confined the agent to the project and the outputs folder.
   The copies in `outputs/render/` are what the user can open; the report should
   cite those. In real use the render folder is `.ui-craft/` in the project, so
   this is a harness artefact — but SKILL.md step 5 should say "the path the user
   can open".
2. **The agent wrote a 20-assertion Playwright script of its own** to check the
   write path (type → clamp → localStorage → dashboard → clear). Legitimate — it
   is behaviour, not measurement — but 14 vitest cases already covered it, and a
   browser script is the expensive way. Cost rule 3 is about probes of the page;
   a sentence that functional checks go into the project's own test runner would
   have saved a turn.
3. **`--compare` was not used**: the dashboard changed and there was no before
   render of it. On a match task that edits an existing page, step 4½'s "prove
   an existing page did not change" row applies to the parts that should not
   have changed; the workflow does not say so.

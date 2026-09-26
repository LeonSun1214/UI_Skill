# Seventh trial — a thin sibling (2026-09-26)

The reading list's `renders` line names the file a thin page hands everything to.
The fifth and sixth trials never needed it: their sibling, Projects, holds its own
markup. This trial picks a sibling that does not: the Blog list page
(`app/blog/page.tsx`, 29 lines) returns `<ListLayout>` from
`layouts/ListLayoutWithTags.tsx` (170 lines), and the reading list says so.

Task: 给这个博客加一个「归档」页面（路由 /archive）：把所有文章按年份分组列出来，每年一个小标题，
每篇一行：日期和标题，标题可点进文章。风格跟 Blog 列表页保持一致，深色模式要正常，导航加入口，别自己发挥。
Plus: prove the Blog list page unchanged apart from the nav. Same harness as the
fifth trial, on a pristine copy of the blog, with 0.11.3.

**Model.** The first attempt ran on the session's earlier model and stopped at the
account's spend limit after one render. The retry ran on a different model, so
the token and time columns below do not compare with the fifth and sixth trials;
the read count does, loosely.

| | trial 5 (Uses page, sibling holds its markup) | trial 7 (archive, thin sibling) |
|---|---|---|
| project files read before the first render | 11 | 6 |
| the file the sibling renders read directly after the sibling | — | yes (`layouts/ListLayoutWithTags.tsx`) |
| tool calls before the first render | 9 | 8 |
| renders / with `--compare` | 5 / 2 | 7 / 3 |
| tokens (comparable) · output | 207k · 60k | 133k · 8.7k (another model) |
| wall clock | 17 min | 11 min |

The six: `app/blog/page.tsx`, `layouts/ListLayoutWithTags.tsx`,
`data/headerNavLinks.ts`, `components/Header.tsx`, `app/tags/page.tsx` and
`.gitignore`. No CSS file, no store, no `package.json`, no `tsconfig`, no other
layout.

Independent grading (the same renderer, a baseline from a second pristine copy):

- `/archive`: 42 text elements, 0 below threshold; dark mode 0; focus 30/30; 1 h1,
  no skipped levels. The FAILs are the template's: the footer's 5 px overflow at
  375 and 20 px nav links.
- `/blog` against the baseline: 0.03–0.08 % changed, *within the header (y 50–70
  px)* at 768 and 1440, identical at 375, the same one console error as before.
  The 0.11.3 location line said in words what the agent had to prove.

The agent's own report matched both. It also opened the mobile menu with `--act`
and found, pre-existing, six menu links with no visible focus ring.

What it exposed:

1. **A generated file moved the baseline.** contentlayer rewrites
   `app/tag-data.json` when the dev server starts and whenever a file under a
   watched folder changes; the order of tags with equal counts varies, so the Blog
   list's tag sidebar differed between the baseline and the after render for
   reasons that were not the agent's. It took the baseline again with the
   generated file restored. *0.11.4:* the compare row in SKILL.md says to restore
   generated files before each of the two renders.
2. **The harness refused a subagent's `.md` file** ("Subagents should return
   findings as text"): the run could not write its `SUMMARY.md`. An eval-harness
   matter, not the skill's; its reply text is in the run's report, and future
   trials should ask for the summary in the final message instead of a file.

**Judged against the Blog list page** (the match rubric, after 0.11.4): fit 4, finish 4,
hierarchy 4, brief 5, overall 4. That is the highest score any trial page has had: "I'd
merge it with at most a small note: make the mobile H1 stand out more from the year
headings". None of the Uses pages scored above 3.

Open: the no-skill and ui-ux-pro-max runs of this task, to see whether they also
find the layout directly or read their way to it.

## The same task with ui-ux-pro-max and with no skill (after 0.11.6)

The archive task run by a fresh agent under each of the other two configurations, on
pristine copies of the blog, with the same model as the ui-craft run above, and graded
the same way: `render.mjs` on each `/archive`, `--compare` of each `/blog` against one
pristine baseline, the match rubric against the Blog list, reads counted from the
transcripts.

| | ui-craft (0.11.3) | ui-ux-pro-max | no skill |
|---|---|---|---|
| text contrast failures on `/archive` | 0 | 0 | 0 |
| targets under 24 px / 24–44 px | 7 / 23 | 7 / 23 | 7 / 23 |
| links without hover feedback | 1 | 1 | 12 |
| Blog list moved | within the header only | within the header only | within the header only |
| judge, match: fit / overall | 4 / 4 | 4 / 4 | 3 / 3 |
| judge pairs, both orders | lost to no skill 0–2, beat pro-max 2–0 | lost both | won both |
| files in the diff | 3 | 3, plus 3 layouts `lint --fix` reformatted | 3 |
| project files named before the first look | **7** | 31 | 41 |
| where the layout file came | 3rd | 4th | 4th |
| tool calls | **39** | 71 | 98 |
| tokens (comparable) | **133k** | 244k | 276k |
| wall clock | **10 min** | 18 min | 20 min |

What it shows:

1. **The pages are the same page.** Every measurement matches, and all three pairs were
   decided at confidence 2, the judge's lowest, on a divider under the title. The judge's
   scores and its pairs even disagree: no skill scores lowest and wins both its pairs.
   There is no visual difference here to claim.
2. **The 12 links without hover on the no-skill page are the sibling's.** The Blog list's
   post titles have no hover style (`ListLayoutWithTags.tsx`, the title link); the unaided
   run matched that, the other two added a hover colour the sibling lacks.
3. **Every run found the layout by following the import**, third or fourth file, right
   after the Blog page. The reading list's `renders` line was not what found it.
4. **What differs is everything else read before the first look:** 7 project files
   against 31 and 41. The unaided run read `tsconfig`, `next.config`, the ESLint and
   Prettier configs, `postbuild.mjs` and all eleven posts; ui-ux-pro-max read most of
   `components/` and `app/`.
5. **ui-ux-pro-max left `lint --fix`'s reformatting of three untouched layouts in its
   diff;** ui-craft (the 0.10.1 rule) and the unaided run reverted it.

Caveats. One run per configuration. The ui-craft run is from 0.11.3, alone on the
machine; the other two ran at the same time, and both lost screenshots to a scratch
folder they shared and took them again, so their time and tokens are inflated by an
amount this cannot separate. The next parallel trial gives each agent its own scratch
folder.

My grading hit the generated-file trap of this trial too: a grading script restored
`app/tag-data.json` after the dev server had rewritten it, while the baseline had been
rendered with the rewritten one, so both Blog lists first compared 0.3–0.8 % changed
"within All Posts". The same protocol for baseline and runs put all three back to the
header only.

Judge cost: $1.40.

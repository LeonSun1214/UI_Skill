# Sixth trial — three configurations on a real repository, the same task (2026-09-25)

The benchmark's numbers (56/56 vs 53/56 vs 50.7/56) come from fixtures. This is the
first three-way comparison on a real repository: the fifth trial's task, on
`timlrx/tailwind-nextjs-starter-blog`, run by a fresh agent under each
configuration with the same prompt, and graded by the same renderer.

Task: 给这个博客加一个「Uses」页面（路由 /uses）：我日常用的东西清单，分「硬件」「软件」「服务」三组，
每组一个小标题，每一项有名称、一句话说明、可选的链接。数据像 projectsData 那样放在 data/ 下的一个文件里，
先填几条示例。导航加入口。风格跟 Projects 页保持一致，深色模式要正常，别自己发挥。 Plus: prove the
Projects page unchanged apart from the nav.

Grading: `render.mjs` on each result's `/uses` (three viewports, dark pass) and on
its `/projects` with `--compare` against a pristine render made by the same renderer;
`judge.py` for the absolute score and both-order pairs on the contact sheets;
tokens from the transcripts; reads counted before the first look at the page.

| | ui-craft 0.10.0 | ui-ux-pro-max | no skill |
|---|---|---|---|
| text contrast failures on `/uses` | **8** | 10 | 10 |
| targets under 24 px / 24–44 px | **7** / 13 | 17 / 22 | 7 / 30 |
| overflow at 375 (the template's footer) | yes | yes | yes |
| dark mode rendered, failures | yes, 0 | yes, 0 | yes, 0 |
| links without hover feedback | 3 | 7 | **1** |
| Projects page moved (max, any screenshot) | 0.15 % | 0.15 % | 0.15 % |
| new errors against the baseline | 0 | 0 | 0 |
| judge, overall 1–5 | 2 | 2 | 3 |
| judge pairs, both orders | lost to pro-max 0–2 · split with no skill | beat both 2–0 | split with ui-craft · lost to pro-max 0–2 |
| tokens (comparable) | 207k | 264k | **188k** |
| wall clock | 17 min | 17 min | **12 min** |
| tool calls | 31 | 49 | 31 |
| project files read before the first look | **11** | 21 | 25 |
| group names as the user wrote them (硬件 / 软件 / 服务) | yes | yes | no — English |
| the Projects card pattern kept | yes | yes | no — a divider list |
| the nav clipping at 768 found and fixed | yes | yes | yes |
| checks clean (`tsc`, `next lint`) | yes | yes | yes |

Every configuration produced a working page, found the same nav clipping at 768,
made the same one-class Header change, reverted lint's drift, and left the
Projects page alone. On this task the three are close, and the margin the
fixtures show does not appear here.

What separates them:

- **Measurements.** ui-craft's page has the fewest contrast failures and the fewest
  small targets. pro-max's page has 17 targets under 24 px: its item names are
  links at `text-xl` line height and its cards carry two links each. The no-skill
  page has 30 targets between 24 and 44 px: a link per item title and a `Learn
  more` per item, in a list.
- **Reading.** 11 files before the first look against 21 and 25: the reading list
  does on a real repository what it could not show on a two-page fixture. pro-max
  and no-skill both read `css/tailwind.css`, `app/layout.tsx`, the theme
  provider, two other pages, a layout, `tsconfig` and the eslint config to learn
  what the *Start here* section states.
- **Cost.** No skill is cheapest and fastest; ui-craft is 10 % more; pro-max is
  27 % more than ui-craft (49 tool calls, 12 images read, seven `tsc` runs).
- **The judge.** pro-max won both pairs, and in every vote for one reason: it
  filled each group with four sample items, so its two-column grid has full
  rows; ui-craft filled three, so the last row holds one card and an empty slot,
  and the judge read that as unfinished. The pages are otherwise, in the judge's
  words, "near-identical Projects-style pages". The no-skill divider list split
  with ui-craft (each order picked the second image) and lost to pro-max.
- **The brief.** ui-craft and pro-max kept the user's Chinese group names and the
  Projects card pattern; no skill translated the names to English and chose a
  list, both stated as decisions.

What changed because of it (0.11.2):

- **`ragged grid` in the audit.** A grid or wrapping flex row whose last row is
  short (three items in two columns) is a warning with the container named, and a
  findings line: fill the sample data or let the last item span. The judge's only
  decisive difference between the two card pages is now a line in the report
  before anyone looks.
- SKILL.md, the look step: sample data fills the rows.

What this trial does not settle: one run per configuration, one task, one
repository. The fixtures' three-run spread was about one assertion per task;
here a single content choice (three samples or four) decided the judge. The
claim the README can make from real repositories is narrower than the fixture
claim: fewer defects and fewer reads at a similar cost, not a wide margin on
what a design lead sees.

## Re-judged with the match rubric (after 0.11.4)

This is a match task: the brief says to follow the Projects page and not to improvise.
The generic rubric scores distinctiveness, and its score prompt never shows the brief.
`judge.py` now has a match rubric. It shows the reference first (a contact sheet of the
page the brief names), scores fit, finish, hierarchy, brief and overall, and asks which
page the site's owner would merge. It counts a new visual idea against a page.

Both rubrics ran on the same model (the one used for the earlier verdicts was out of
credit) and the same contact sheets. A fourth page went in as a control: the same
content as the Uses page, styled with a gradient hero, italic serif headings, violet
rounded cards and pill buttons. It is striking, and nothing like the site.

| | generic, overall | match: fit · finish · hierarchy · brief · overall |
|---|---|---|
| ui-craft | 2 | 4 · 3 · 4 · 4 · **3** |
| ui-ux-pro-max | 2 | 4 · 3 · 3 · 4 · **3** |
| no skill | 2 | 4 · 4 · 3 · 4 · **3** |
| off-brief control | 2 | 1 · 3 · 3 · 4 · **1** |

| pair, both orders | generic | match |
|---|---|---|
| ui-craft vs no skill | split (each order picked the first image) | **ui-craft 2–0** (confidence 4, 3) |
| ui-craft vs ui-ux-pro-max | ui-ux-pro-max 2–0 (2, 2) | ui-ux-pro-max 2–0 (2, 2) |
| no skill vs ui-ux-pro-max | ui-ux-pro-max 2–0 (4, 3) | ui-ux-pro-max 2–0 (3, 4) |
| ui-craft vs control | ui-craft 2–0 (4, 4) | ui-craft 2–0 (5, 5) |

What it shows:

1. **The generic score cannot see the brief.** It gives the control the same overall 2 as
   the three pages that followed the brief. The match score gives the control 1 and the
   others 3, and its notes say why: "This doesn't read as the same site." The generic
   pair prompt does quote the brief, so it already preferred the matching page to the
   control; the match rubric raised that from confidence 4 to 5.
2. **A position split resolved.** Under the generic rubric, ui-craft against no skill was
   a split in which each order picked the first image; the earlier model split the same
   pair the other way round. Under the match rubric both orders pick ui-craft: its bordered
   cards follow the Projects page, the unaided divider list does not.
3. **ui-ux-pro-max still wins its pairs**, now for the fuller grid and item titles closer
   in size to the Projects cards. It wins at confidence 2 against ui-craft, the lowest the
   judge gives.
4. **All three real pages score overall 3** ("belongs but needs a round of notes"). Fit 4
   for all three. Finish is where they differ: no skill 4, the other two 3.

Cost: 25 judge calls, $3.58 ($1.59 for the generic rubric, $1.99 for the match rubric and
the archive page). The earlier generic verdicts, from the other model, are kept beside the
new ones as `judge-fable.json` and `judge-pairs-fable.json`.

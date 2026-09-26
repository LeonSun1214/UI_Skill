# Eighth trial — the archive task on Nuxt (2026-09-26)

0.12.0 taught the inspector Nuxt and wrote `references/stacks/nuxt.md`, checked on
fixtures and templates but never by an agent doing a task. This trial gives a fresh
agent the seventh trial's task on the Nuxt UI SaaS template (Nuxt 4.5, Nuxt UI 4.11,
@nuxt/content 3.16; six posts, 2018–2024):

给这个网站加一个「归档」页面（路由 /archive）：把所有博客文章按年份分组列出来，每年一个小标题，
每篇一行：日期和标题，标题可点进文章。风格跟 Blog 列表页保持一致，深色模式要正常，导航加入口，别自己发挥。

Same harness as the seventh trial: a subagent, the skill path, the task verbatim, a
clean copy on a branch of its own, `nuxt dev` started by the agent, the project's own
checks (`npm run typecheck`, `npm run lint`, both passing on the clean copy), no
questions. One run, with ui-craft, on the model of the seventh trial's retry.

## What it made

`app/pages/archive.vue` (86 lines) and seven lines of nav: Archive after Blog in
`AppHeader.vue`, and in `app/utils/links.ts`, the ⌘K palette's copy of the nav.
It also added `.ui-craft` to `.gitignore`. The page is the Blog list's frame
(`UContainer`, `UPageHeader` with the same `py-[50px]`, `UPageBody`). Each year is
an `h2` in `UBlogPost`'s title classes. Each row has the date in the card's date
classes and format, and the title as a `ULink`. Only semantic classes
(`text-highlighted`, `text-toned`, `hover:text-primary`), no palette classes.
Typecheck and lint pass (rerun here).

Graded by re-rendering:

- **Blog list against a clean baseline:** 6 of 9 screenshots identical. The 3 at
  1440 changed only within the header (y 20–40 px), where the new nav item is.
  Errors: the same 7 as the baseline, all external images the sandbox blocks.
- **The new page:** no finding of its own. Every FAIL is in the header or footer,
  and the same on the Blog list. Its six title links carry `ULink`'s default ring,
  primary at 25 % (1.35:1), like every link on the site, and like the Blog list's
  post cards, which draw theirs on the card around the link (see below).

The agent named the faint rings as inherited. It said to fix them once, in
`app.config.ts` (`ui.link.base`), which is right: the theme's base is
`outline-primary/25`, and `Link.vue` merges `appConfig.ui.link` over it.

Its decisions, stated in the reply:

- dates read in UTC, since a calendar day in local time moves west of Greenwich;
- the header text written into the page rather than a new content file;
- the palette entry.

## The reading list, followed

| call | what |
|---|---|
| 1 | SKILL.md |
| 2 | `inspect.py` |
| 3 | the Blog list page and its parent, `AppHeader.vue`, and `references/stacks/nuxt.md`: the files the reading list pointed to |
| 4–6 | `content.config.ts` and the blog's content file; then where else the nav lives: a grep for `/blog`, `AppFooter.vue`, `app/utils/links.ts`, `app.vue`, `error.vue` |
| 7–8 | `nuxt dev`, waited for |
| 9 | first render: the Blog list, as the baseline, before any edit |

Nine project files before the first look, against six in the seventh trial. Four of
the nine were the hunt for every copy of the nav, which the reading list does not
name; two were the content collection's config and the blog's content file.
The stack notes' Nuxt UI section did its job: the agent built with the kit's
components and semantic classes, and handled the kit's defaults as inherited, both as
`nuxt.md` says.

## What it cost, and where

| | trial 7 (Next.js) | trial 8 (Nuxt) |
|---|---|---|
| tool calls | 39 | 49 |
| tool calls before the first render | 8 | 8 |
| renders / with `--compare` | 7 / 3 | 5 / 2 |
| tokens (billed) · output | 133k · 8.7k | 204k · 30k |
| wall clock | 10–11 min | 17 min |

The extra calls:

- **4 calls in Nuxt UI's bundle:** it went looking for the blog card's title and
  date classes in `node_modules/@nuxt/ui/dist` (270 KB of every component). Nuxt
  generates `.nuxt/ui/blog-post.ts`, 4 KB, with the same classes. `nuxt.md` now
  says so.
- **6 `report.json` queries:** four to learn whether its own title links were
  among the faint rings and small targets, one for the mobile menu's dialog audit,
  one for the Blog list's errors. The findings block showed each
  section's first 4–6 lines without saying it had stopped. The counts behind the
  Verified line were capped at 20: "20 rings below 3:1" was 30, and the probes
  stop at 30 tab stops and 20 hovers without saying so. Each section now ends
  with how many it left out and the `report.json` path that holds them. The
  counts are no longer capped, and the Verified line names the probe limits.
- **4 extra calls on edits:** two edits failed because the files had been read
  with `cat`, not the Read tool; it read them and redid the edits. That is the
  harness, not the skill.
- **1 render of the mobile menu:** it opened the menu with `--act` and audited it
  as a dialog. That goes beyond the brief, and is fair.

## A renderer bug, found while grading

The first baseline of the Blog list compared badly: 99.87 % changed on the 375 dark
screenshot. That screenshot was light. On the dev server's first, cold load, Nuxt's
colour-mode plugin hydrated after the dark pass had switched the page. It then put
back the theme it had read at boot, between the dark audit (which measured dark
colours) and the screenshot. One dark screenshot in 27 across this trial. The dark
pass now puts `.dark` back before each later step, and checks that the screenshot
shows the colours it measured (else a warning). `selftest/late-theme.html` replays
it: under 0.12.0 its dark screenshot is light.

A second sandbox effect: avatars whose images are blocked fall back to initials only
once the image fails, so a render taken sooner shows six fewer contrast findings.
Baselines for grading are now rendered on a warmed-up server; this one is in
`blog-baseline-warm`.

## Two more measurement gaps, found by checking a claim

These notes first said the Blog list's post cards show no focus ring. The renderer
said so: 6 of its 24 tab stops "invisible". The cards do have one. `UBlogPost`'s
link has `focus:outline-none` and is stretched over the card, and the card root
draws the ring with `has-[>a:focus-visible]:outline-3`, in primary at 25 %. The focus
probe looked at the focused element and its pseudo-elements, not at the card around
it. It now also snapshots the three elements above each one. A parent whose outline
or shadow changes on focus (`:focus-within`, `:has(a:focus-visible)`) is the ring:
"outline on a parent 1.35:1". A parent that changes only its background shows focus
without a ring to measure. The Blog list now reads 24 of 24 with a visible ring, all 24
faint, which is what its theme says.

The same pattern made a false small target. A link stretched over its card takes
clicks on the whole card. Tailwind UI does it with an `absolute inset-0` span inside
the link, Bootstrap with a `::after` at inset 0. The target size was taken from the
link's own box, its line of text (19 px). The card now counts as the target, when
the overlay covers the link's own box; a hidden tooltip inside a button does not.

`selftest/layers.html` has both cards. On the four React pages of the earlier
regression check nothing changed, apart from the "… N more" lines and the named
probe limits.

## The same task under ui-ux-pro-max and with no skill

Two more fresh agents, with the prompts of the seventh trial's three-way, side by
side, each on its own copy, port and output folder (the seventh trial's pair shared a
scratch folder). The ui-craft run above ran alone, on 0.12.0. All three pages were
graded again with 0.12.2 against the warm baseline.

**The three pages are one page.** All three use the Blog list's frame. Each year is
an `h2` in `UBlogPost`'s title classes, and each post a row with the date in the
card's date classes, formatted in UTC. All three put the nav entry in
`AppHeader.vue` and in the ⌘K copy in `links.ts`. The differences:

- ui-craft's title links are 44 px rows;
- ui-ux-pro-max made the title hover an underline in primary, since blue text on
  hover is 3.76:1, and added a `scroll-padding-top` for the sticky header on this
  page only;
- no skill put the header text in a new content file and collection, the pattern
  Blog and Changelog use, and gave its `NuxtLink` `ULink`'s focus classes.

Measured, the pages are the same except one count: 14 targets between 24 and 44 px
on ui-craft's page, 20 on the other two, whose rows are shorter. On all three, the
Blog list changed only within the header at 1440, typecheck and lint pass (rerun
here), and every FAIL is in the header or footer.

**The judge**, match rubric with the Blog list as reference, scores them overall
3 · 3 · 4 (ui-craft, ui-ux-pro-max, no skill). Its "finish" scores (2, 3, 4) mark down
the same thing on all three: the half-empty column at 1440 they share. Head to head,
ui-craft beats no skill in both orders (confidence 2, then 3). ui-craft against
ui-ux-pro-max splits, and so does ui-ux-pro-max against no skill. The pairs turn on
the subtitle's wording and on titles wrapping at 375 px. As in the seventh trial,
scores and pairs disagree: the judge cannot separate pages this close.

| | ui-craft | ui-ux-pro-max | no skill |
|---|---|---|---|
| project files read before the first look | 9 | 35 | 29 |
| first look at call | 9 | 37 | 19 |
| tool calls | 49 | 106 | 74 |
| tokens (billed) · output | 204k · 30k | 287k · 29k | 201k · 20k |
| tokens per turn | 4.9k | 3.4k | 3.3k |
| wall clock | 17 min, alone | 27 min | 17 min, side by side |

What the other two read first:

- **ui-ux-pro-max:** the file tree and 35 files, down to the CI workflow and all
  six posts. Five skill searches (`--stack nuxt-ui`, `--domain ux`), none of which
  shows in the page. Nuxt UI's bundle and `BlogPost.vue`, and the content database.
- **No skill:** 29 files, then Nuxt UI's generated theme files, found on its own
  (`.nuxt/ui/*.ts`, which `nuxt.md` now points to), and the kit's `BlogPost.vue`
  and `Link.vue`.

Against the seventh trial (Next.js): ui-craft 133k → 204k, ui-ux-pro-max 244k →
287k, no skill 276k → 201k. On Nuxt, ui-craft's reading list saved reads (9 against
29) and calls (49 against 74), but not tokens. Its turns cost half as much again as
the unaided agent's, because its context carries SKILL.md, the inspector's output
and five render reports. Part of that was the 0.12.1 gaps: the bundle, and the
`report.json` lookups.

## One claim, checked

The agents told the user different things about a bug they did not touch:

- **No skill:** in China the Blog list shows every date a day early.
- **ui-craft:** the two pages agree in China, and only the Americas are off.
- **ui-ux-pro-max:** Los Angeles is off, and said nothing about China.

Rendered under `Asia/Shanghai`, the Blog list shows "Aug 24, 2023" for a post dated
2023-08-25, with 13 hydration warnings. The unaided agent had measured it,
emulating time zones from UTC+14 to UTC−11. ui-craft asserted without measuring, and
was wrong. The cause is in the kit: the Blog page passes `UBlogPost` a formatted local
string, which `UBlogPost` parses again as local midnight and formats in UTC. So the
list is a day early everywhere but UTC. The one-line fix all three proposed
(`timeZone: 'UTC'` in the Blog page) would not fix it east of UTC; passing
`post.date` itself would. The renderer has no time-zone option, so the loop could
not have caught this. A claim about another time zone was the one place the skill's
"measure, don't guess" did not reach.

## The hover probe, found while grading

ui-ux-pro-max's titles show hover with an underline that appears by colour
(`decoration-transparent` → `decoration-primary`). The hover probe compared the line
of the decoration, not its colour, and did not look at `::before` / `::after` (an
underline that grows on `::after` is common). It reported six false "no hover
feedback". It now compares the decoration's colour, thickness and offset, and the
pseudo-elements; `selftest/layers.html` has both kinds.

## Not answered

- The judge cannot separate pages this close. On a match task this constrained,
  what differs between the configurations is what they cost and what they tell the
  user, not how the page looks.
- ui-craft's cost per turn: the renders' output is the largest thing it carries.
  Findings grouped by part of the page (header, main, footer) would shorten the
  output and answer "is this mine" at once.
- The reading list does not say where the nav is defined. All three found the ⌘K
  copy anyway, by reading.
- A render in another time zone (`--timezone`) would have let ui-craft check its
  claim about China instead of making it.

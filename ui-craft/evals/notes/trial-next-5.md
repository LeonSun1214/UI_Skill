# Fifth real-repository trial — a fresh agent on a Next.js blog (2026-09-25)

The fourth pass (`trial-next-4.md`) ran the tools on two public Next.js apps by
hand and rewrote the reading list for them. This one measures whether a fresh
agent following SKILL.md 0.10.0 gets the benefit: same harness as the third trial
(a subagent, the skill path, the task verbatim, outputs to a folder, no questions),
on `timlrx/tailwind-nextjs-starter-blog` (Next 15.5 App Router, React 19,
Tailwind 4, next-themes, contentlayer2).

Task, as a user would put it: 给这个博客加一个「Uses」页面（路由 /uses）：我日常用的东西清单，
分「硬件」「软件」「服务」三组，每组一个小标题，每一项有名称、一句话说明、可选的链接。数据像
projectsData 那样放在 data/ 下的一个文件里，先填几条示例。导航加入口。风格跟 Projects 页保持一致，
深色模式要正常，别自己发挥。 Plus: prove the Projects page unchanged apart from the nav.

| | trial 3 (Sunnote, Vite, 0.9.0) | trial 5 (blog, Next.js, 0.10.0) |
|---|---|---|
| wall clock | 15 min | 17 min |
| tokens (comparable) | 381k | 207k |
| tool calls in all | — | 31 |
| tool calls before the first render | 16 | 9 (skill at #1, inspect.py at #2) |
| project files read before the first render | 9 | 11 (projectsData, headerNavLinks, projects/page, Card, Header, MobileNav, Link, sitemap, package.json, .gitignore, the dev log) |
| renders | 2 | 5 (baseline, three of the new page, the sibling with `--compare`) |
| render host | — | `localhost` from the first render |
| `--compare` used on the sibling | no | yes: 375 0 %, 768 0.14 %, 1440 0.09 %, no height change — the nav only |
| critique | — | skipped, by the rule (the page copies a sibling's layout) |
| project checks | typecheck + 110 tests | `tsc --noEmit` clean, `next lint` 0/0 |

Result: `data/usesData.ts` in the shape of `projectsData` (three groups, `name` /
`description` / optional `href`), `app/uses/page.tsx` copying the Projects page
shell (same h1, tagline, `divide-y`, container) with one `h2` per group and the
`Card` border-and-padding for items, the nav entry, the sitemap entry, and one
class on `Header.tsx` (`md:max-w-72` → `md:max-w-84`) because the template caps
the desktop nav and a fifth link clipped "About" to "At" at 768 — seen in its own
contact sheet, disclosed as a one-class revert. Dark mode 0 failures. The 8 text
failures on the page are the template's `text-primary-500` links (3.58:1), kept
for consistency with Projects and reported with the one-line fix. No new colour,
radius or shadow; the Chinese copy in the system fallback face, said so.

Every number in its summary was checked against its `report.json` and the diff:
all true. The page matches the sibling to the class.

What the trial exposed:

1. **The dev server's overlay was in the measurements.** Next's "1 Issue" badge
   (a `<nextjs-portal>` whose button lives in a shadow root) sat in every
   screenshot, and, since Playwright's selectors pierce shadow roots, in the hover
   audit ("2 without feedback": the badge and the logo) and the focus audit
   ("focus obscured" behind it). The agent attributed both correctly and spent
   words on it. *0.10.1:* hidden before paint with Vite's `<vite-error-overlay>`,
   reported as hidden, errors still counted.
2. **A type check restarted the dev server under a render.** `tsc --noEmit` wrote
   `tsconfig.tsbuildinfo`, Next rebuilt, and the render in flight measured a
   half-built page; the agent noticed, re-rendered, and ran `tsc` five times and
   lint four in all. *0.10.1:* a row in step 4½ — the project's checks run after
   the last render; a lint script with `--fix` reformats files the task never
   touched, revert those.
3. **The reading list did its job on a layout-driven app**, without the `renders`
   line being needed: the sibling here (Projects) is not a thin page, so the
   agent read it and its `Card` directly. Whether `renders` saves reads on a thin
   sibling (a page that hands everything to a layout) is still unmeasured.
4. **Tokens halved against the third trial** (207k vs 381k) on a task of the same
   shape. Two things differ: the reading list and the merged findings block, and
   a Next.js repository whose pages are small. Not separable here; the number that
   would separate them is a second run of the third trial's task on 0.10.x.

Open: a match task whose sibling *is* a thin page (the blog's `/about` renders
`AuthorLayout` from MDX), to measure the `renders` line; and the judge on this
output against a without-skill run of the same task, which no trial has done on a
real repository yet.

## Where the tokens went (transcript profile, added after 0.11.0)

19 assistant turns. Billed 207k: 40.6k on the first turn (the cache write of the
system prompt, the task and SKILL.md — SKILL.md is 25k characters, about 6.5k of
it), 59.8k of output, 146.8k of cache writes. The output is the largest lever:
the code (≈130 lines), the summary and the commands come to roughly a quarter of
it; the rest is deliberation, and every output token is written back into the
cache as context the next turn. Fewer turns is the only way down.

Turns the tools could have saved, now saved: one chasing the `308` on `/projects`
(`trailingSlash: true`, which the reading list now states); two comparing the
console errors of the baseline and the new page by hand (`--compare` now does
it and says "the same 1 as the baseline"); one re-render after `tsc` restarted
the dev server (the 0.10.1 rule). One `cat package.json` of 77 lines the reading
list had already summarised (rule 6 now names it). Together about four of
nineteen turns, and the deliberation that came with them.

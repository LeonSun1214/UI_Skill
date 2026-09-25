# Second real-repository trial — Sunnotice, the review path (2026-09-25)

Task, as a user would put it: 团队页在手机上不好用，看看有什么问题，能修的修掉。Real
FastAPI backend in demo mode (a throwaway SQLite), a session obtained through the
API's impersonate call and passed with `--cookie`, the splash lifted by the same
init script as the first trial. Two renders (before, after with `--compare`), one
critique. About 25 minutes including the backend setup; the reading was the page's
own 710 lines and nothing else.

What the loop found on a page its author had already measured with a contrast
script of their own: a 66 × 20 team switcher and 30 × 22 theme segments in the
header of every page (under the 24 px floor); thirty 32 px text buttons on the
roster cards — the actions a thumb reaches for; member names as h3 under an h1;
and, at 375, the demo-mode "Time travel" pill covering a card's Deactivate button
mid-scroll (the focus-obscured probe). Text contrast: 103 elements, 0 below,
both themes — the project's glass discipline holds. After the fixes: 0 targets
under 24 px, 15 between 24 and 44 (all header chrome), no skipped level, and the
page 200 px taller at 375.

What broke or misled:

1. **A session that did not stick measured the wrong page, silently.** The first
   impersonate call sent `{id}` where the API wanted `{member_id}`; the cookie
   was empty; the render measured the sign-in page and reported it with the same
   confidence — 5 contrast failures that belonged to the login roster, "0 h1".
   Nothing in the output said which page had rendered. *Fixed in 0.8.3:* the
   output's first lines name the page (`page: "…" · h1 …`) and flag a sign-in
   title.
2. **The critic on a review task fights the product.** Scores 2 / 3 / 2 / 3 / 2,
   *would not ship*; its three changes: demote the primary button's gradient,
   pad the page under a demo-only floating pill, and make the glass cards 55 %
   translucent — the last one undoing a decision the README proves with a
   contrast argument (94 % opaque, measured). None was inside the ask; all three
   were listed, none applied. The brief I gave it had six lines about the look
   and nothing about the project's rules. *Written into 4d in 0.8.3:* on an
   established project the brief carries the project's stated rules, one line
   each.
3. **`--compare` numbers are true and hard to read.** 17–27 % of pixels changed
   because 44 px targets made the page taller and everything below shifted. A
   layout shift and a colour change score the same. A per-region diff, or the
   height delta first ("+200 px at 375, then 16 % changed"), would read better.
   Open.
4. **Bonus finding, not the page under review:** the sign-in page's demo roster
   draws each initial in `text-ink` on the member's colour — 2.0:1 on amber,
   2.4:1 on emerald, 2.6:1 on sky, 3.4:1 on rose in the light theme, 4.0:1 on
   indigo in the dark one — while the app's own `Avatar` picks black or white
   per colour. Reported to the owner; outside the ask.

The mocks of the first trial were not needed: with the backend up, the page had
its real data, the right counts and the sky. Where a backend can be started,
start it.

# First real-repository trial — Sunnotice (2026-09-25)

Task, verbatim: 给 Sunnotice 做一个封面介绍页和修改创建团队页 … 风格：简约，符合应用定位，
有个性，iOS 风。Vite + React 18 + Tailwind 3, a FastAPI backend, two themes set by a
`data-theme` attribute from a boot script, a splash that covers the first two seconds,
every string typed against a Chinese dictionary. Delivered as a PR.

What the loop caught that code review would not: the primary button wrapping to
three lines at 768 and 1440 (a flex child that shrank), a 20 px link, a status
endpoint the store calls that the mocks did not answer, and — from the critic — a
headline stranding one word, an eyebrow that leaked the accent colour, a helper
line competing with the pitch, and a 1440 fold that cut the sky tiles mid-row.

What broke or misled, in the order met:

1. **The installed copy was stale.** `~/.claude/skills/ui-craft` was a 0.4-era
   SKILL.md (no critique, no direction.py); the Skill tool loaded that one. The
   repo copy at 0.8.1 was followed by hand. `install.sh` needs re-running after
   every version; the description should say which version loaded.
2. **`inspect.py` on the workspace root** reported "no recognised UI stack" instead
   of listing `frontend/` as the app package (the monorepo table in SKILL.md
   promises the listing). Running it on `frontend/` worked.
3. **`verify.py` read imports out of comments**: two FAILs naming packages
   `'what was the newest\n   * event'` and `'missed'`, both words inside JSDoc.
   Strip comments before scanning.
4. **The dark pass never reached a boot-script theme.** `emulateMedia` in place is
   invisible to a script that read `matchMedia` once at load and set
   `data-theme`; the "dark" audit measured the light page (the Verified block
   did say `(unchanged!)`, which is how it was noticed). Fixed in this trial:
   when the colours do not move, the page is reloaded under the dark scheme
   and measured again. Selftest still 11/11.
5. **Non-text contrast on a gradient-filled control** reported the icon of the
   selected theme segment at 1:1 "against rgb(15,23,41)": the button's fill is a
   gradient, and the measure fell through to the page colour. Text contrast
   already marks gradient backgrounds unverifiable; non-text should too.
6. **Focus rings under `outline-style: auto`** were reported at 1.06:1 in the
   dark theme on every control (the project has no `:focus-visible` rule outside
   its sky mode, so Chromium draws its two-tone default ring). The computed
   `outline-color` is not what is painted. Treat `auto` as a UA ring: visible,
   not measured.
7. **A selected segment (`aria-pressed="true"`) counts as "no hover feedback".**
   The probe exempts `aria-current` and disabled controls; it should exempt
   pressed and checked ones too.
8. **The critique rule reads "not on match tasks in an established project"**;
   a brand-new landing page in an established project is a match task by the
   inspector's verdict and a taste task by any other reading. Ran it (twice, the
   cap); both verdicts were *would not ship*, each time for a different, valid
   reason. The second round's three changes were applied without a third call.
   Worth a sentence in 4d: match the tokens, critique the composition.
9. **The splash.** Nothing in the loop dismisses an intro animation; an
   `--init-script` that dispatches a key event did. A `--dismiss <selector|key>`
   flag would be cleaner than asking the model to invent that.

Spend: four renders of the cover page, two of the no-team page, two critiques
(≈ $0.18), one `npm run build`. Wall clock about 70 minutes including reading
the project, which was most of it.

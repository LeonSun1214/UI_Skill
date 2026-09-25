# Sprint 8 — an independent critic, the review path, and variance

## 8a — critique.mjs: a second pair of eyes in the loop

`scripts/critique.mjs` sends the contact sheet (and the brief in one line) to a fresh
`claude -p` session that has seen no code and made none of the decisions; it returns
six rubric scores, a ship / don't-ship verdict and three concrete changes. SKILL.md
step 4d runs it on pages whose look matters (greenfield, redesign, "make it look
better"), treats the changes like FAILs and owes one more round for any dimension at
3 or below; once per round, twice per task; never on match tasks in an established
project. Smoke test on the v4 eval-1 page: the critic found a section seam cutting
through the invoice card at 1440, two competing filled CTAs, and 9–10px invoice type
at 375 — none of which the builder's own look had raised. Version 0.8.0.

## 8b — eval-5: review and fix an existing page

Fixture `evals/fixtures/review`: a working 等位通 admin queue page with nine planted
defects (gray-400 text at 2.5:1, 20px unnamed icon buttons, `focus:outline-none`
nav, a nine-column table overflowing to 594px at 375, zoom blocked, a pulsing dot
without a reduced-motion rule, h1→h3, an avatar without alt, status by colour
alone). Prompt: 运营同事说这页在手机上不好用、键盘操作不了、看不清，审一遍，能修的都修掉。
15 assertions, four new (`zoom-allowed`, `headings`, `status-text` via a visible-text
sample render.mjs now records, `found-issues` = the report names ≥ 6 of the 10).

| | ui-craft v5 | ui-ux-pro-max | no skill |
|---|---|---|---|
| assertions | 15/15 | 15/15 | 15/15 |
| planted issues named | 9/10 | 9/10 | 9/10 |
| tokens (comparable) | **162k** | 275k | 180k |
| time | **640 s** | 963 s | 734 s |

Reading: when the *task* says "audit this page", a strong model builds its own
instruments — no-skill found the global Playwright install and wrote an overflow /
target / contrast / focus walker; pro-max wrote a 4-viewport audit script and even
rediscovered the `transition-colors` outline fade that Sprint 3 had fixed in
render.mjs. All three fixed everything. The skill's advantage on this path is that
the instrument already exists: 14% fewer tokens and 13% less time than no-skill,
41% / 34% less than pro-max, with the same result — and the same numbers every time,
which a hand-rolled script is not. "The nine issues were all found" is therefore not
a claim the skill can make alone; "found in one render with a verdict block you can
paste" is.

## 8c — variance: three runs per configuration on evals 1–3

Nine fresh ui-craft v5 runs (three per eval on 1–3), two more no-skill runs per
eval (run-1 is iteration-1's), ui-ux-pro-max left at its single iteration-1 run
per eval — its cells are n=1. Every run judged; pairwise on run-1 against run-1.
Eighteen agent runs this sprint: 3.09M billed tokens (3.62M comparable), against
the 1.2M first estimated; judge and critique calls another ≈ $14 outside that.

| | ui-craft v5 | ui-ux-pro-max (n=1) | no skill |
|---|---|---|---|
| eval-1 greenfield | 14/14 · 260k ±41k · look 4 (n=3) | 11/14 · 222k · look 3 | 10.3 ±0.9/14 · 189k ±20k · look 3.7 ±0.5 (n=3) |
| eval-2 match | 14/14 · 126k ±14k · look 3 (n=3) | 14/14 · 147k · look 3 | 14/14 · 111k ±15k · look 3 (n=3) |
| eval-3 de-template | 13/13 · 250k ±21k · look 4 (n=3) | 13/13 · 235k · look 4 | 11.3 ±1.2/13 · 228k ±32k · look 4 (n=3) |
| eval-5 review | 15/15 · 162k · look 3 | 15/15 · 275k · look 3 | 15/15 · 180k · look 3 |
| **pass** | **56/56** | **53/56** | **50.7/56** |
| tokens, comparable, evals 1–3 | 212k | 201k | 176k |
| judge overall, evals 1–3 | 3.67 | 3.33 | 3.56 |
| pairwise vs ui-craft v5, evals 1–3 | — | 0–2, 1 split | 0–3 |
| pairwise, eval-5 | — | pro-max | no skill |

What three runs say that one could not:

1. **The assertion gap is structural, not luck.** ui-craft: ten runs, ten at full
   marks, spread 0. No-skill's misses repeat: every eval-1 run shipped the system
   font stack, a report without numbers and a logo link with no hover state; two of
   three eval-3 runs had 20 px nav links and a focus ring at 1.04:1 / 1.49:1, one had
   body text at 3.77:1. 56 vs 50.7 holds run to run; the ±0.9 / ±1.2 is which of
   those misses, not whether.
2. **v5 costs more than v4 on the taste tasks**, and the spread is wide enough that
   v4's single runs sit inside it: eval-1 260k ±41k vs 229k, eval-3 250k ±21k vs
   202k. Against the other two on evals 1–3: +5% on ui-ux-pro-max, +20% on no skill.
   On the match path (no critique) 126k, between the two.
3. **The absolute judge has a ceiling.** No 5 in 23 runs; 15 of 23 score 4/4/4/3/4
   (spacing is its standing complaint); all six ui-craft and no-skill runs on eval-3
   are score-identical. On that scale v5 (3.67) and a strong unaided model (3.56)
   are level, and v5 is where v4 was. Pairwise still separates them: v5's run-1 beat
   no-skill on all three evals (v4: 1–1, 1 split) and pro-max on two with one split
   (unchanged). One run a side, so each pair is one draw — the direction agrees with
   8a's premise, it does not prove it.
4. **eval-5 goes the other way.** Both pairs pick the other page, for the same
   reasons in both orders: no active nav state, call / delete as bare icons at 768
   and 1440, the two actions at equal weight in the mobile cards. The other two
   polished the hierarchy (labelled bordered buttons, status pills); ui-craft fixed
   exactly the ten defects and, by rule, ran no critique on a review in an existing
   project. The rule was wrong for that case — a critique call is nine cents.

The price of the critique, corrected from the interim guess:

- One call, measured: **$0.09 and 34 s** (`claude -p`, one image). `judge.py`'s
  calls on the same sheets with the same model cost $0.29–0.45 — longer answers —
  so budget up to half a dollar a call. It is outside the token accounting.
- Calls per run: eval-1 3 / 2 / 2, eval-3 3 / 2 / 2 (each 3 includes one retry after a
  reply that was not JSON); none on eval-2 and eval-5. Renders per run: eval-1
  4 / 4 / 3, eval-3 7 / 3 / 4.
- What the owed rounds bought, read off the critic's own verdicts: after a *would
  not ship*, the next round flipped it to *would ship* in three of four cases
  (eval-1 r1, eval-3 r1, eval-1 r3); eval-3 r3 went not-ship → not-ship, typography 3
  giving way to spacing 3. After a *would ship* with one dimension at 3 (eval-1
  r2), the round the rule demanded returned the same six scores for ≈ 45k tokens.
- Time: 15–24 min per taste-task run (eval-1 1438 / 1158 / 1102 s, eval-3 1430 /
  869 / 1198 s) against 13–21 min unaided.

## 8d — changed on the strength of 8c (0.8.1)

- **Round rule.** A round is owed when the critic would not ship it, or when two or
  more dimensions sit at 3 or below; one 3 under a ship verdict is a note for the
  report. `critique.mjs` prints the verdict in those terms.
- **Review tasks get one critique**, after the fixes; its three changes are
  findings — fixed when inside the ask, listed otherwise. Changed on one eval's
  pairwise verdict; unverified until the next review run.
- `grade.py` skips a run until its `SUMMARY.md` exists (a run in progress had been
  graded on its first screenshots). `summarize.py` prints no spread for identical
  runs and fractional totals to one decimal.
- The sprint notes and each iteration's summary table are copied into
  `evals/notes/` so the record outlives the workspace.

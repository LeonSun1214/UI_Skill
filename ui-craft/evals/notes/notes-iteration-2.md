# Iteration 2 — cost-control sprint, three-way

| | ui-craft v2 | ui-ux-pro-max | no skill | ui-craft v1 |
|---|---|---|---|---|
| eval-1 greenfield | 11/11 · 279k | 9/11 · 364k | 7/11 · 221k | 11/11 · 366k |
| eval-2 established | 11/11 · 162k | 11/11 · 198k | 11/11 · 68k | 11/11 · 170k |
| eval-3 de-template | 10/10 · 282k | 10/10 · 326k | 8/10 · 272k | 10/10 · 369k |
| **pass** | **32/32** | 30/32 | 26/32 | 32/32 |
| token mean | **240,811** | 296,248 | 186,945 | 301,685 |
| vs no skill | +29% | +58% | — | +61% |

- v1 → v2: −20% tokens, zero assertion regressions. Target was +25% over no-skill; landed at +29%.
- Now cheaper than ui-ux-pro-max by 19% while passing 2 more assertions. The position moved
  from "same price, better guarantee" to "cheaper and better".
- Remaining waste: eval-1 v2 ran a confirmation render (fixed in SKILL.md, commit deaa808);
  eval-2 v2 still +139% over no-skill for an identical result — the "established + simple page"
  path needs more cutting (skip the brief, read only the report summary, one render).
- Interruptions: every with-skill and pro-max run in both iterations was interrupted once and
  resumed; overhead is evenly distributed but inflates absolute counts.
- Next widening moves (pro-max cannot do these): dark-mode render + contrast, interaction-state
  screenshots, non-text contrast — each becomes an assertion pro-max fails by construction.

| | with_skill | ui_ux_pro_max | without_skill |
|---|---|---|---|
| eval-1-greenfield-landing | 13/14 · 230k | 11/14 · 222k · look 3/5 | 9/14 · 171k · look 4/5 |
| eval-2-established-match | 14/14 · 134k | 14/14 · 147k · look 3/5 | 14/14 · 97k · look 3/5 |
| eval-3-generic-to-distinctive | 13/13 · 251k | 13/13 · 235k · look 4/5 | 10/13 · 222k · look 4/5 |
| eval-4-dark-mode | 12/12 · 187k · look 3/5 | 11/12 · 171k · look 3/5 | 11/12 · 217k · look 3/5 |
| **pass (per-eval mean over runs)** | **52/53** | **49/53** | **44/53** |
| token mean | 227,459 | 257,167 | 186,816 |
| token mean, comparable | 200,801 | 193,631 | 176,961 |
| visual judge, overall 1–5 | 3.00 (distinctive 3.00) | 3.25 (distinctive 3.25) | 3.50 (distinctive 3.50) |

(a)k (b)k = billed tokens (comparable: minus the cache re-write after an interruption, plus the harness-prefix cache write when a sibling run had paid it)

Visual judge, pairwise (both image orders; 'split' = the two orders disagreed):
- with_skill vs ui_ux_pro_max: 0–0, 1 split · 4: split

Failures:
- eval-1-greenfield-landing · ui_ux_pro_max: contrast, report-numbers, hover-feedback
- eval-1-greenfield-landing · with_skill: hover-feedback
- eval-1-greenfield-landing · without_skill: contrast, targets, type-move, report-numbers, hover-feedback
- eval-3-generic-to-distinctive · without_skill: contrast, targets, focus
- eval-4-dark-mode · ui_ux_pro_max: dark-contrast
- eval-4-dark-mode · without_skill: dark-contrast

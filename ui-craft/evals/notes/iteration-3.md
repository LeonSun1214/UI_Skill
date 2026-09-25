| | with_skill | ui_ux_pro_max | without_skill |
|---|---|---|---|
| eval-1-greenfield-landing | 14/14 · 229k · look 4/5 | 11/14 · 222k · look 3/5 | 9/14 · 171k · look 4/5 |
| eval-2-established-match | 14/14 · 152k · look 3/5 | 14/14 · 147k · look 3/5 | 14/14 · 97k · look 3/5 |
| eval-3-generic-to-distinctive | 13/13 · 202k · look 4/5 | 13/13 · 235k · look 4/5 | 10/13 · 222k · look 4/5 |
| **pass (per-eval mean over runs)** | **41/41** | **38/41** | **33/41** |
| token mean | 174,060 | 296,248 | 186,945 |
| token mean, comparable | 194,483 | 201,322 | 163,593 |
| visual judge, overall 1–5 | 3.67 (distinctive 3.67) | 3.33 (distinctive 3.33) | 3.67 (distinctive 3.67) |

(a)k (b)k = billed tokens (comparable: minus the cache re-write after an interruption, plus the harness-prefix cache write when a sibling run had paid it)

Visual judge, pairwise (both image orders; 'split' = the two orders disagreed):
- with_skill vs ui_ux_pro_max: 2–0, 1 split · 1: with_skill; 2: with_skill; 3: split
- with_skill vs without_skill: 1–1, 1 split · 1: without_skill; 2: split; 3: with_skill

Failures:
- eval-1-greenfield-landing · ui_ux_pro_max: contrast, report-numbers, hover-feedback
- eval-1-greenfield-landing · without_skill: contrast, targets, type-move, report-numbers, hover-feedback
- eval-3-generic-to-distinctive · without_skill: contrast, targets, focus

| | with_skill | ui_ux_pro_max | without_skill |
|---|---|---|---|
| eval-1-greenfield-landing | 12/14 · 257k | 11/14 · 222k · look 3/5 | 9/14 · 171k · look 4/5 |
| eval-2-established-match | 12/14 · 200k | 14/14 · 147k · look 3/5 | 14/14 · 97k · look 3/5 |
| eval-3-generic-to-distinctive | 11/13 · 308k | 13/13 · 235k · look 4/5 | 10/13 · 222k · look 4/5 |
| **pass (per-eval mean over runs)** | **35/41** | **38/41** | **33/41** |
| token mean | 301,685 | 296,248 | 186,945 |
| token mean, comparable | 254,816 | 201,322 | 163,593 |
| visual judge, overall 1–5 | — | 3.33 (distinctive 3.33) | 3.67 (distinctive 3.67) |

(a)k (b)k = billed tokens (comparable: minus the cache re-write after an interruption, plus the harness-prefix cache write when a sibling run had paid it)

Failures:
- eval-1-greenfield-landing · ui_ux_pro_max: contrast, report-numbers, hover-feedback
- eval-1-greenfield-landing · with_skill: hover-feedback, non-text-contrast
- eval-1-greenfield-landing · without_skill: contrast, targets, type-move, report-numbers, hover-feedback
- eval-2-established-match · with_skill: hover-feedback, non-text-contrast
- eval-3-generic-to-distinctive · with_skill: hover-feedback, non-text-contrast
- eval-3-generic-to-distinctive · without_skill: contrast, targets, focus

| | with_skill | ui_ux_pro_max | without_skill |
|---|---|---|---|
| eval-1-greenfield-landing | 14/14 · 260k ±41k · look 4/5 (n=3) | 11/14 · 222k · look 3/5 | 10.3 ±0.9/14 · 189k ±20k · look 3.7 ±0.5/5 (n=3) |
| eval-2-established-match | 14/14 · 126k ±14k · look 3/5 (n=3) | 14/14 · 147k · look 3/5 | 14/14 · 111k ±15k · look 3/5 (n=3) |
| eval-3-generic-to-distinctive | 13/13 · 250k ±21k · look 4/5 (n=3) | 13/13 · 235k · look 4/5 | 11.3 ±1.2/13 · 228k ±32k · look 4/5 (n=3) |
| eval-5-review-and-fix | 15/15 · 162k · look 3/5 | 15/15 · 275k · look 3/5 | 15/15 · 180k · look 3/5 |
| **pass (per-eval mean over runs)** | **56/56** | **53/56** | **50.7/56** |
| token mean | 179,116 | 283,189 | 161,618 |
| token mean, comparable | 207,071 | 219,760 | 176,355 |
| visual judge, overall 1–5 | 3.60 (distinctive 3.50) | 3.25 (distinctive 3.00) | 3.50 (distinctive 3.50) |

(a)k (b)k = billed tokens (comparable: minus the cache re-write after an interruption, plus the harness-prefix cache write when a sibling run had paid it)

Visual judge, pairwise (both image orders; 'split' = the two orders disagreed):
- with_skill vs ui_ux_pro_max: 2–1, 1 split · 1: with_skill; 2: with_skill; 3: split; 5: ui_ux_pro_max
- with_skill vs without_skill: 3–1, 0 split · 1: with_skill; 2: with_skill; 3: with_skill; 5: without_skill

Failures:
- eval-1-greenfield-landing · ui_ux_pro_max: contrast, report-numbers, hover-feedback
- eval-1-greenfield-landing · without_skill: contrast, targets, type-move, report-numbers, hover-feedback
- eval-1-greenfield-landing · without_skill: type-move, report-numbers, hover-feedback
- eval-1-greenfield-landing · without_skill: type-move, report-numbers, hover-feedback
- eval-3-generic-to-distinctive · without_skill: contrast, targets, focus
- eval-3-generic-to-distinctive · without_skill: targets, focus

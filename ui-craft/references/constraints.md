# Constraints — measurable rules and where they come from

These are the rules that get UI rejected in review or fail an audit. Each has a
threshold, a note on whether `scripts/render.mjs` measures it, and a link to its
source. When memory and the source disagree, the source wins.

`✓` measured by render.mjs · `~` partial / heuristic · `manual` read the code or look.

## Text and contrast

| Rule | Threshold | Check | Source |
|---|---|---|---|
| Text contrast (AA) | ≥ 4.5:1 body · ≥ 3:1 large text (≥ 24px, or ≥ 18.66px bold) | ✓ | [WCAG 2.2 · 1.4.3](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) |
| Non-text contrast: control boundaries, icons, focus rings, chart marks | ≥ 3:1 against adjacent colors | manual | [WCAG 2.2 · 1.4.11](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) |
| Meaning never by color alone (status, required, error) | add icon, text, or pattern | manual | [WCAG 2.2 · 1.4.1](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) |
| Text over images or gradients | verify the worst pixel, or add a scrim | ~ (reported as unverifiable) | 1.4.3 above |
| Zoom to 200% without loss | no clipping, no overlap | manual | [WCAG 2.2 · 1.4.4](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html) |
| Survives text-spacing overrides (line-height 1.5, paragraph 2×, letter 0.12em, word 0.16em) | no clipping | manual | [WCAG 2.2 · 1.4.12](https://www.w3.org/WAI/WCAG22/Understanding/text-spacing.html) |

## Targets and pointer

| Rule | Threshold | Check | Source |
|---|---|---|---|
| Target size, minimum (AA) | ≥ 24×24 CSS px, or a 24px spacing circle · inline text links exempt | ✓ | [WCAG 2.2 · 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) |
| Target size, enhanced (AAA) | ≥ 44×44 CSS px | ✓ warn | [WCAG 2.2 · 2.5.5](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html) |
| Platform minimums | iOS 44×44 pt · Android 48×48 dp | ✓ warn at 44 | [Apple HIG · Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility) · [Material 3 · Accessibility](https://m3.material.io/foundations/accessible-design/accessibility-basics) |
| Dragging has a single-pointer alternative (reorder, sliders, maps) | buttons or inputs exist | manual | [WCAG 2.2 · 2.5.7](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html) |
| Nothing depends on hover — touch has none | tooltips and menus also open on tap or focus | manual | [WCAG 2.2 · 1.4.13](https://www.w3.org/WAI/WCAG22/Understanding/content-on-hover-or-focus.html) |

## Keyboard and focus

| Rule | Threshold | Check | Source |
|---|---|---|---|
| Focus is visible | a visible change on every focusable element | ✓ | [WCAG 2.2 · 2.4.7](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html) |
| Focus not obscured by sticky or fixed UI | focused element at least partly visible — `scroll-padding-top: <header height>` | ✓ | [WCAG 2.2 · 2.4.11](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html) |
| Focus appearance (AAA, a good default) | ≥ 2px perimeter · ≥ 3:1 change | manual | [WCAG 2.2 · 2.4.13](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html) |
| Rings on `:focus-visible`, not `:focus` · never `outline: none` without a replacement | — | ~ | [MDN · :focus-visible](https://developer.mozilla.org/en-US/docs/Web/CSS/:focus-visible) |
| Skip link to main content | first focusable element | ✓ | [WCAG 2.2 · 2.4.1](https://www.w3.org/WAI/WCAG22/Understanding/bypass-blocks.html) |
| Every control has an accessible name — icon buttons `aria-label`, inputs a `<label>` | — | ✓ | [WCAG 2.2 · 4.1.2](https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html) |
| Focus order follows visual order · dialogs trap and then restore focus | — | manual | [WCAG 2.2 · 2.4.3](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html) |

## Motion

| Rule | Threshold | Check | Source |
|---|---|---|---|
| Respect `prefers-reduced-motion` | disable non-essential animation · keep the final state | ✓ (rule present) | [WCAG 2.2 · C39](https://www.w3.org/WAI/WCAG22/Techniques/css/C39) · [2.3.3](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html) |
| Auto-moving content over 5s can be paused or stopped (carousels, tickers) | control present | manual | [WCAG 2.2 · 2.2.2](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html) |
| Nothing flashes more than 3× per second | — | manual | [WCAG 2.2 · 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html) |
| Animate `transform` and `opacity`, not layout properties | — | manual | [web.dev · animations guide](https://web.dev/articles/animations-guide) |

## Layout and reflow

| Rule | Threshold | Check | Source |
|---|---|---|---|
| Reflow: no horizontal scroll at 320 CSS px (data tables excepted) | scrollWidth ≤ viewport | ✓ at 375 · check 320 for AA | [WCAG 2.2 · 1.4.10](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) |
| Viewport meta present · zoom not blocked | no `user-scalable=no`, no `maximum-scale=1` | ✓ | [MDN · viewport meta](https://developer.mozilla.org/en-US/docs/Web/HTML/Viewport_meta_tag) · 1.4.4 |
| Layout shift | CLS < 0.1 — reserve space for images, embeds, fonts (`width`/`height`, `aspect-ratio`, `font-display`) | manual | [web.dev · CLS](https://web.dev/articles/cls) |
| Safe areas on notched devices | `env(safe-area-inset-*)` on fixed bars | manual | [MDN · env()](https://developer.mozilla.org/en-US/docs/Web/CSS/env) |
| Heading structure: one `h1`, no skipped levels · landmarks `main`, `nav` | — | ✓ | [WCAG 2.2 · 1.3.1](https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships.html) · [2.4.6](https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels.html) |

## Forms

| Rule | Threshold | Check | Source |
|---|---|---|---|
| Visible label on every field — a placeholder is not a label | `<label for>` or wrapping label | ✓ (unnamed controls) | [WCAG 2.2 · 3.3.2](https://www.w3.org/WAI/WCAG22/Understanding/labels-or-instructions.html) |
| Errors identified in text, next to the field, and announced | `aria-describedby` + `aria-invalid` | manual | [WCAG 2.2 · 3.3.1](https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html) · [GOV.UK · error message](https://design-system.service.gov.uk/components/error-message/) |
| Error summary at the top of multi-field forms, focus moved to it | — | manual | [GOV.UK · error summary](https://design-system.service.gov.uk/components/error-summary/) |
| Don't ask for the same information twice in one flow | autofill or carry forward | manual | [WCAG 2.2 · 3.3.7](https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry.html) |
| Login without a cognitive test — allow paste and password managers | — | manual | [WCAG 2.2 · 3.3.8](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html) |
| `autocomplete` on identity fields | `name`, `email`, `tel`, `postal-code`, `new-password` … | manual | [WCAG 2.2 · 1.3.5](https://www.w3.org/WAI/WCAG22/Understanding/identify-input-purpose.html) |
| Help (contact, chat) in the same place on every page | — | manual | [WCAG 2.2 · 3.2.6](https://www.w3.org/WAI/WCAG22/Understanding/consistent-help.html) |

## Images and icons

| Rule | Threshold | Check | Source |
|---|---|---|---|
| Every `<img>` has `alt` — descriptive, or `alt=""` when decorative | — | ✓ | [WCAG 2.2 · 1.1.1](https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html) · [WAI · decorative images](https://www.w3.org/WAI/tutorials/images/decorative/) |
| Decorative SVG icons are `aria-hidden="true"` · meaningful ones have a name | — | manual | [WAI-ARIA APG · names and descriptions](https://www.w3.org/WAI/ARIA/apg/practices/names-and-descriptions/) |
| One SVG icon family · never emoji as UI icons (renders differently per platform, no color control) | — | manual | convention |

## Conventions — not standards, labeled so you know

| Rule | Why |
|---|---|
| Body text ≥ 16px · form inputs ≥ 16px | iOS Safari zooms into inputs with smaller text on focus |
| Line length 45–75 characters (`max-width: 65ch`) | readability — [Butterick · line length](https://practicaltypography.com/line-length.html) |
| Hover / UI transitions 150–300ms · larger movements ≤ 500ms | perceived responsiveness; longer feels sluggish |
| Viewports to check: 375, 768, 1024, 1440 | phone, tablet, laptop, desktop — without chasing every device |
| `cursor: pointer` on custom clickable elements (`<button>` defaults to `default`) | affordance |
| Tabular numbers in tables and stat tiles (`tabular-nums`) | columns align |

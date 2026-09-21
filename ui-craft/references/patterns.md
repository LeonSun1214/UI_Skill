# Patterns — what each page type owes the user

Structure and behaviour per page type. These aren't templates: the section order is
a starting point, the behaviours are obligations. Jump to the section you need.

- [Landing / marketing](#landing--marketing)
- [App shell and dashboard](#app-shell-and-dashboard)
- [Forms and settings](#forms-and-settings)
- [Auth](#auth)
- [States: empty, loading, error](#states-empty-loading-error)
- [Tables and lists](#tables-and-lists)
- [Modals, drawers, popovers](#modals-drawers-popovers)

## Landing / marketing

**Order that usually works:** hero (what + for whom + one action) → proof or product
shot → 2–4 benefits framed as outcomes → how it works (3 steps at most) → social
proof → pricing or final CTA → footer. Cut any section you can't fill with real content.

**Owes the user**
- One primary action, repeated: small in the nav, in the hero, and at the end. Secondary actions look secondary.
- The headline says what it is; the sub says for whom or what changes. Never "Welcome to".
- Real proof or none: invented logos, stats, and quotes are worse than a missing section.
- Any carousel or auto-rotating proof: previous/next buttons, a pause control, stops on hover and focus, a static frame under reduced motion, position announced. Or don't rotate it.
- A sticky nav must not obscure focus (`scroll-padding-top`) and must not eat the mobile viewport (keep it ≤ 64px).

**Decide explicitly:** text-left with visual right, or centered; one full-bleed
section or none; pricing on the page or on its own; whether a hero visual exists yet —
if not, typography carries the fold (see `anti-generic.md`).

**Common failures:** four things competing above the fold; features listed instead of
outcomes; the CTA color also used on links and icons; a 96px headline that becomes six
lines at 375.

## App shell and dashboard

**Structure:** persistent nav (sidebar at ≥ 1024, bottom bar or drawer below) → page
header (title as `h1`, breadcrumb or context, primary action on the right) → content
at a consistent max width and gutter. No marketing whitespace: density is a feature.

**Owes the user**
- Where am I: the current nav item is distinct (not by color alone); the page title is the `h1`.
- Live or refreshing data is labeled: last-updated time, a stale state when it's old, a pause or refresh control, no background polling while the tab is hidden, a static snapshot under reduced motion.
- Numbers: tabular figures, consistent units and decimals, deltas with a sign and a color *and* an arrow or word.
- Charts: legend or direct labels; ≥ 3:1 between series colors; a text alternative (table or summary).
- Every data view has an empty state, a loading state (a skeleton matching the final layout, so nothing shifts), and an error state with retry.
- Filters and sort survive reload (in the URL) where that matters.

**Decide explicitly:** sidebar collapsed by default or not; card-per-widget or a
rule-separated grid; light surface unless the product is used in low light.

**Common failures:** marketing spacing inside an app (everything 64px apart); five
grays with no system; a KPI row where the biggest number isn't the most important;
charts with a rainbow of series.

## Forms and settings

**Structure:** one column. Related fields grouped under a heading and a short
description. Primary action at the end, aligned with the fields (or in a sticky bar
for long forms); destructive actions far from it.

**Owes the user**
- A visible label above every field. A placeholder is a hint, never the label.
- Helper text below the field *before* a mistake; error text in the same place after, with `aria-describedby` and `aria-invalid`.
- Validate on blur or submit, not on every keystroke; never clear what they typed.
- Multi-field errors: a summary at the top that receives focus and links to each field.
- Mark required fields — or mark optional ones instead when most are required.
- The right input type and `autocomplete` (`email`, `tel`, `new-password`, `postal-code`) so mobile keyboards and password managers work.
- Settings show the current value. Save explicitly with confirmation, *or* auto-save with a visible "Saved" — never silently.
- Destructive actions confirm with the consequence stated and the thing named: "Delete 'Q3 report'?"

**Common failures:** two-column forms that break tab order; a toggle with no label for
what "on" means; a Save button that's always enabled; errors shown only in red with no text.

## Auth

**Structure:** one task per screen (sign in *or* create account, each linking to the
other), the product name and one line of context, the fields, the primary action,
the alternative paths below.

**Owes the user**
- `autocomplete="username"` / `current-password` / `new-password`; paste allowed; a show-password toggle.
- No cognitive test (WCAG 3.3.8): no memorize-and-retype; OTP inputs accept paste.
- Errors that don't reveal whether an account exists: "Email or password is incorrect."
- Forgot-password and OAuth visible without hunting; OAuth buttons use the provider's real mark.
- Works at 375 without scrolling to find the button.

## States: empty, loading, error

Every view that shows data has three more states than the happy path. Design them
with the view, not after.

- **Empty, first use:** say what will appear here and give the one action that fills it. An illustration is optional; the action is not.
- **Empty, filtered to nothing:** say the filter matched nothing and offer to clear it. Different from first use.
- **Loading:** a skeleton in the exact final layout (no layout shift). A spinner only for under a second or for indeterminate actions. Say what's loading when it's slow.
- **Error:** what happened in plain words, what they can do (retry, go back, contact), and keep their input.
- **Partial:** some data loaded, some failed — show what you have and mark what's missing.

## Tables and lists

- Column headers are real `<th>`; sortable columns show the direction with an icon *and* `aria-sort`.
- Numbers right-aligned and tabular; text left; never center body cells.
- Row actions visible on hover *and* focus, or always visible on touch; an overflow menu with an accessible name.
- Narrow widths: a table that must stay a table scrolls horizontally *inside its own container* (allowed for data tables) with a visible affordance; otherwise reflow to cards with the most important field first.
- Selection: a checkbox column with a select-all that shows indeterminate; a bulk-action bar that appears with the count.
- Long lists: pagination or virtualization. "Load more" is fine; infinite scroll needs a reachable footer.

## Modals, drawers, popovers

- Only for tasks that need full attention or that must keep page context. If it's a page, make it a page.
- Focus moves into the dialog on open, is trapped, and returns to the trigger on close. `Esc` closes; the backdrop closes non-destructive dialogs.
- A visible title (`h2`) the dialog is labelled by; a close button with a name.
- Below ~640px a centered modal usually becomes a bottom sheet or full screen.
- Popovers and tooltips open on hover *and* focus, dismiss on `Esc`, and can be hovered without disappearing (WCAG 1.4.13).

# Anti-generic — the defaults you reach for, and how to get off them

## Why this happens

Models and template kits converge on the same UI because it's the mode of the
distribution: indigo primary, Inter, white cards on gray-50, a centered hero with
two buttons, three feature columns with icons in tinted circles. None of it is
*wrong*. It's just what everything looks like, so it carries no information about
*this* product. A visitor reads "template" in under a second, and template means
"not real yet".

The goal isn't to be strange. It's to make one or two decisions that could only
have been made for this product, and keep everything else quiet enough that those
decisions are visible.

## The tells

Check the draft against this list. Three or more hits means it's a template.

1. **Indigo / violet / blue-600 primary** with no reason tied to the product.
2. **Inter or system-ui everywhere**, no display face. The page has no voice.
3. **Hero = centered h1 + subhead + two buttons + gradient blob or dot-grid background.**
4. **Three feature cards**, each an icon in a tinted circle above a short title and two lines.
5. **"Trusted by" logo strip** with placeholder logos.
6. **Testimonial cards**: circular avatar, name, title, five stars, big quotation marks.
7. **`rounded-xl` + `shadow-sm` on everything**, so every element is a pill or a card.
8. **Gradient text** on the headline. **Purple → pink gradient** on the CTA.
9. **Glass / blur** applied because it's available, not because something is behind it.
10. **Emoji as icons**, or two icon families mixed.
11. **Copy that could sell anything**: "Streamline your workflow", "Powerful features",
    "Built for teams", "Get started for free" — with no object.
12. **Stats row** — "10k+ users · 99.9% uptime · 24/7 support" — invented to fill the layout.
13. **Dark mode by default** on a product with no reason to be dark.
14. **Perfect symmetry everywhere**: every section centered, every grid 3-up, no
    variation in rhythm from top to bottom.

## Getting off the default: one deliberate move

Pick **one** of these as the "Distinctive" line in the brief. One move executed
consistently beats three half-done.

**Type as identity.** A display face with character — a high-contrast serif, a
condensed grotesque, a geometric with quirks, a mono for a developer product — for
headlines only, paired with a neutral body face. Headline sizes that are actually
large (64–96px at desktop) with tight leading. Cheapest move, highest return.

**Color as a decision.** One accent chosen *for a reason you can say out loud* — the
color of the thing: sage for a plant app, signal orange for an alerting tool, ink
blue for a writing tool — on a neutral base that isn't gray-50. Warm neutrals (stone,
sand) and cool ones (slate, zinc) read differently; pick one on purpose. Then spend
the accent on *actions only*.

**Layout as rhythm.** Break the centered stack: a left-aligned hero with the visual
bleeding off the right edge; an asymmetric 5/7 split; one full-bleed band between
contained sections; a sticky sidebar on a long page. Vary section width and density
so the scroll has a pulse.

**Restraint as style.** Remove the cards. Remove the shadows. Group with hairline
rules and whitespace. Let type and a single accent do everything. This reads as
confidence, and it's the hardest look to fake with a template.

**Material as texture.** A real photograph or illustration treated consistently
(duotone, a fixed crop ratio, a border); a subtle grain; a deliberate 2px border in
the ink color. Only when the product genuinely has material to show.

## Say it through a reference

Name a real product or site whose *feel* matches what this product should feel
like, and write down two specific traits you're borrowing. Not "like Linear" —
"Linear's restraint: hairline borders instead of cards, and one accent used only on
primary actions." You're not copying; you're forcing yourself to be specific about
what "good" means here.

## Copy is part of the UI

Replace every generic line with the specific one. "Streamline your workflow" → "Pull
last month's Stripe charges into one invoice." "Powerful features" → the feature.
If the user hasn't given specifics, ask, or write visibly placeholder copy in
brackets rather than plausible-sounding nothing. Invented proof (logos, stats,
quotes) is worse than a section that doesn't exist yet.

## Don't over-correct

The failure on the other side is noise: three display faces, a gradient *and* a
texture *and* asymmetry, every section a different idea. Distinctive means one
clear decision with everything else in its service. If the rubric pass says the
page is busy, you made too many moves — remove until one remains.

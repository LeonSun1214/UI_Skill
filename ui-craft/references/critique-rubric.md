# Critique rubric — how to look at a screenshot

Open the screenshot and go through this in order. It follows the order a designer's
eye actually moves: whole → structure → detail. Answer each question with what the
pixels show, not what the code intended. Write every "no" down as a concrete
change ("h1 to 56px, lede to 18px muted" — not "improve hierarchy"). Three to five
changes per pass is normal for a first draft. Zero means you didn't look.

Use `1440-fold.png` for sections 1–2, `1440-full.png` for 3–8, `375-full.png` for 9.

## 1. First three seconds (fold only)

Squint, or imagine the screenshot at thumbnail size.

- What do you see first? Is it the thing the page exists for — the headline, the
  primary action, the product? If a decorative element, a logo row, or a nav item
  wins, the hierarchy is inverted.
- What's second and third? There should be a clear 1 → 2 → 3. If four things
  compete, nothing leads.
- Can you tell what this product is and what to do next without reading body text?
- Does the fold end on something that invites scrolling (a card cut off, a section
  heading peeking in), or on a hard horizon that says "that's all"?

## 2. Hierarchy

- Is the size jump between levels big enough to be *seen* rather than measured?
  Display → heading → body usually needs at least a 1.5× step. 24px next to 20px
  reads as an inconsistency, not a level.
- Do weight and color change between levels too, or is size doing all the work?
- How many distinct text styles are on screen? Count them. More than five or six
  and the page has no system.
- Is the primary CTA the single most saturated, highest-contrast interactive
  element on screen — and is there exactly one of it per view?

## 3. Spacing and rhythm

- Is spacing from a scale (4 / 8 / 12 / 16 / 24 / 32 / 48 / 64) or arbitrary? Two
  gaps that are *almost* equal (20 and 24) look like a mistake — make them equal or
  clearly different.
- Proximity: are related things closer to each other than to unrelated things? A
  label sits nearer its field than to the previous field. A section heading sits
  nearer its content than to the section above.
- Section separation vs internal padding: the space *between* sections should be
  clearly larger than the space *inside* a card or group — usually 2×. If they're
  equal, the page reads as one undifferentiated stack.
- Any cramped spots (text touching a border, an icon crowding its label)? Any dead
  zones (an empty band with nothing to justify it)?

## 4. Alignment and grid

- Do left edges line up? Take the left edge of the headline and trace down — body,
  buttons, cards, footer should share it or sit on a deliberate indent.
- Optical alignment: circles, icons, and italics need to be nudged to *look* aligned.
  A 24px icon beside 16px text usually wants its center on the text's x-height, not
  its baseline.
- Are card contents aligned across a row — all titles at the same y, all buttons on
  the bottom edge — or does each card float independently?
- Is anything slightly off-center? Slightly is worse than clearly.

## 5. Weight and balance

- Where is the visual weight? Dark blocks, saturated color, dense text, and big
  images are heavy. Is the weight where the eye should rest, or piled in one corner?
- Is the composition balanced across the width? A two-column hero with text on the
  left and nothing on the right is half a page.
- Are shadows and borders one system? Either everything has a hairline border, or
  everything has one shadow level. Three shadow sizes plus occasional borders reads
  as unfinished.

## 6. Typography

- Measure: body text between roughly 45 and 75 characters per line. Wider is
  fatiguing; narrower chops sentences. `max-width: 65ch` on prose is the usual fix.
- Line height: body ~1.5–1.6; headings ~1.1–1.2. A display headline at 1.5 looks
  like a paragraph.
- Is there a display face doing something the body face can't? Or is one grotesque
  doing everything (see `anti-generic.md`)?
- Widows in headlines — one word alone on the last line. Fix with
  `text-wrap: balance` or a manual break.
- Are numbers in tables and stat tiles tabular (`font-variant-numeric: tabular-nums`)
  so they align?

## 7. Color

- Does the accent have one job (actions), or is it also decorating icons, borders,
  and headings until it means nothing?
- Are the neutrals doing the structural work — surfaces, borders, muted text — so
  the accent can stay rare?
- Is any color used semantically (red, green, amber) where it's only decorative, or
  decoratively where it should be semantic?
- On tinted backgrounds, does muted text still read? `report.json` has the number;
  here, does it *look* readable?

## 8. Components and states

- Do buttons look pressable — enough padding, a clear label, one height across the page?
- Are hover, focus, and active states visible, or does the page exist in one state
  only? (`report.json` lists buttons that change nothing on hover; here, judge whether
  the changes that exist are *legible* — a 2% darkening is not feedback.)
- If the page has a dark mode, open `contact-dark.png` and re-ask sections 2, 5 and 7:
  hierarchy often collapses in dark (everything mid-gray), shadows disappear so
  borders must do the grouping, and the accent that was rare on white can glow.
- Do cards earn their border or shadow, or would the content read better as plain
  sections? Card inside card inside card is the most common tell of not deciding.
- Icons: one family, one stroke width, one size scale? Decorative icons that add
  nothing are noise — remove them.
- Empty, loading, and error states: if the view shows data, where do they go? Not
  visible in a screenshot — check the code.

## 9. The narrow column (375-full)

- Does the stacking order still tell the story? Hero text → action → proof, not hero
  image → four paragraphs → action.
- Is anything tiny now? Tap targets, captions, and badges that were fine at 1440.
- Any horizontal scroll or clipped content? `report.json` says; confirm visually.
- Are the biggest headlines still proportionate, or do they wrap into six lines?
- Is the primary action reachable without scrolling past everything?

## 10. Sameness check

Look at the whole page and ask: if this were one of ten SaaS sites in a row, what
would make someone stop on this one? If nothing, open `anti-generic.md` and make
one deliberate move. Not five.

## 11. Write the change list

One line per item — *what · where · why*:

```
- h1 to 52px, lede to muted 18px · hero · the two currently compete
- align card CTAs to the bottom edge · pricing grid · they sit at three heights
- collapse three shadow sizes to one (shadow-sm) · whole page · reads unfinished
```

Then apply, re-render, and look again.

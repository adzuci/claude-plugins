# Apollo GTME Design Tokens — Extended Reference

Values extracted from the reference decks. Pints for PPTX; the helpers in
`apollo_brand.py` already encode the canvas, palette, and fonts.

## Canvas

```text
10.0 x 5.625 in  (16:9). SLIDE_W / SLIDE_H in apollo_brand.
```

## Fonts (with fallbacks)

```text
Display : Space Grotesk  (fallback Arial)     titles, hero, section heads, chip numbers
Body    : DM Sans         (fallback Arial)     body copy, bullets, card text
Mono    : DM Mono         (fallback Consolas)  labels, metrics, SFDC names, eyebrows, footers
```

## Type Scale (points)

```text
Hero / cover      48-96    Space Grotesk bold
Slide title       26-32    Space Grotesk bold
Sub-head          14-18    Space Grotesk
Body              11-13    DM Sans
Label / metric    8-10     DM Mono (often All-Caps)
```

Pick the size that fits the card. Small body text is intentional — it is how the
reference decks fit dense layouts. Do not inflate to a minimum.

## Palette (role -> hex)

```text
ink 1A1A1A   white FFFFFF   muted 736F6C   muted-2 94918E   muted-3 47423D
paper F3F0EE   paper-2 F2F0EB   paper-3 F7F5F2   night 243031
sun F8FF2C   sun-deep E1F000   sun-pale FEFFD9
mist CCC9C6   lavender C9C6D3   steel 3A6783   lime C8CC3C
success 22C55E   danger EF4444   amber F59E0B   (semantic, sparing)
```

## Border Radius (rounded-rectangle adjustments[0])

```text
Card:  ~0.06-0.18   Pill / chip: ~0.4-0.5 (fully rounded)
Keep it consistent within a deck.
```

## Shadow

```text
Selective, not on every card. ~25-30 shadowed shapes across a 15-24 slide deck.
Use to lift the primary card on a slide, not every box.
```

## Spacing

```text
Chrome margin 0.35in from edges. Left accent bar 0.06in wide, full height, sun.
Snap card gaps to a consistent rhythm (~0.2-0.3in between stacked cards).
```

## Letter Spacing

```text
Mono labels / eyebrows: All-Caps, slight positive tracking.
Body: normal. Headlines: normal to slightly tight.
```

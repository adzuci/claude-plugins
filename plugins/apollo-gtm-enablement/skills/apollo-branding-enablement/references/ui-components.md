# Apollo GTME UI Component Patterns — Extended Reference

Card-based components from the reference decks. Build each as a rounded-rectangle
card (no text on the card shape) plus separate `add_text` layers on top. All
sizes in points; positions in inches on the 10 x 5.625 canvas.

## Numbered chip (agenda / steps)

```text
shape:   oval or rounded square, ~0.40in
fill:    sun-deep (E1F000)
text:    Space Grotesk bold ~13pt, ink, centered
use:     agenda row numbers, workflow step numbers
```

## Eyebrow label

```text
font:    DM Mono ~11pt, All-Caps, ink (or muted-3 on cards)
use:     section/category label above a slide title
```

## Definition card ("WHAT IT IS")

```text
card:    mist (CCC9C6) fill, radius ~0.08, shadow on the primary card
label:   DM Mono ~11pt All-Caps, muted-3
body:    DM Sans ~13pt, ink, word-wrap + autofit
```

## Pale-yellow callout card (trigger / key signal)

```text
card:    sun-pale (FEFFD9) fill, radius ~0.08
label:   DM Mono ~11pt All-Caps
value:   DM Mono ~12-13pt (e.g. a metric or SFDC field name)
note:    DM Sans ~10-11pt, muted
use:     one highlighted signal per content slide, max
```

## Labeled metric row (sidebar)

```text
card:    mist fill, ~0.5in tall row
label:   DM Sans ~11pt, ink, left
value:   DM Mono ~11pt, muted-3, right-aligned
use:     timing sidebar, KPI list, trigger attributes
```

## Workflow chain

```text
steps:   mist cards (~0.48in tall) stacked, each "N  Label" (DM Sans/Mono)
arrows:  down-arrow glyph between cards, ink, ~10pt
final:   highlight the terminal step with a sun-deep card
```

## Timing / agenda sidebar

```text
card:    mist fill, tall
header:  "60 MINUTES" DM Mono ~11pt bold
rows:    section name (DM Sans) + duration (DM Mono, right)
```

## Section divider

```text
background: sun or night
title:      large Space Grotesk bold (48-64), "N. Title"
```

## Engagement activity slide

```text
background: sun (F8FF2C)
badge:      ENGAGEMENT ACTIVITY — small stone pill, white/off-white text
headline:   Space Grotesk bold, large (48-72), ink
watermark:  optional faint stone outline mark, large, corner
```

## Host / placeholder circle

```text
shape:  circle, ink at low opacity, placeholder only — never generate faces
sizes:  1 host large, scale down as host count grows
```

## Evidence / quote card (Gong)

```text
card:   paper-3 or mist, radius ~0.08
quote:  DM Sans ~13pt, ink
clip:   DM Mono All-Caps chip "CLIP 1 OF 2"
keep the clip label clear of the title (>50% overlap fails verify_deck)
```

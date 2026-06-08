---
name: apollo-branding-enablement
description: Apollo brand reference for GTM Enablement PPTX decks. Activated by apollo-gtm-enablement plugin commands. Use when building or polishing any Apollo GTME deck. Gives the design DNA (palette, fonts, type scale, card patterns, chrome) from the reference decks that look good, lets you design each slide freely with python-pptx, and guarantees the output renders cleanly via a post-build verifier.
disable-model-invocation: true
---

# Apollo GTME Branding Reference

This skill does NOT cage your design. You write a fresh `python-pptx` script per
deck and own every layout decision — like the reference decks that look good were
made. What this skill gives you:

1. A **design reference** (below) — the real palette, fonts, type scale, card
   patterns, and chrome from the reference decks. Imitate it; don't recreate a
   generic renderer.
1. A **light, optional toolkit** (`scripts/apollo_brand.py`) — canvas/palette/font
   constants and a few helpers (`set_background`, `add_text`, `card`, `chip`,
   `add_chrome`). Use them or compose shapes yourself. Nothing is rejected.
1. The **functional guarantee** — `verify_deck(path)`. Run it after building. It
   catches the glitch class that broke past decks (text off-slide, text-on-text
   collisions, non-rendering fonts). Fix what it flags and rebuild.

The guarantee is in verification AFTER the build, not in restrictions BEFORE it.
Design stays free; output stays correct.

**Reference decks are the north star.** Two known-good example decks were shared
by the original owner (Scott). Match their density, card style, and tone.

______________________________________________________________________

## DESIGN DNA (extracted from the reference decks)

### Canvas

`10.0 x 5.625 in` (16:9). Set on the Presentation, not per-shape:
`deck.slide_width = SLIDE_W; deck.slide_height = SLIDE_H`.

### Fonts (with fallbacks — fonts may not be installed on the viewer's machine)

| Role | Font | Fallback | Used for |
|---|---|---|---|
| Display | Space Grotesk | Arial | titles, hero, section heads, chip numbers |
| Body | DM Sans | Arial | body copy, bullets, card text |
| Mono | DM Mono | Consolas | labels, metrics, SFDC names, code, eyebrows, footers |

Always set `run.font.name` explicitly. `verify_deck` flags any other font.

### Type scale (points) — small and dense, NOT a rigid scale

```
Hero / cover       48-96   Space Grotesk bold
Slide title        26-32   Space Grotesk bold
Sub-head           14-18   Space Grotesk
Body               11-13   DM Sans
Label / metric     8-10    DM Mono (often All-Caps)
```

Use whatever size makes the content fit its card. Small body text (10-13pt) is
how the reference decks fit dense, card-based layouts. Do not inflate to a
"minimum" — oversized text is what caused overflow in the broken version.

### Palette (role -> hex; pass either to the helpers)

```
ink       1A1A1A   primary text on light            paper     F3F0EE  primary light bg
white     FFFFFF   text on dark                     paper-2   F2F0EB  cream variant
muted     736F6C   secondary text                   paper-3   F7F5F2  lightest cream
muted-2   94918E   captions                         night     243031  dark bg / cover
muted-3   47423D   dark muted                        sun       F8FF2C  primary yellow accent
mist      CCC9C6   neutral grey card                sun-deep  E1F000  numbered chips, done nodes
lavender  C9C6D3   section tint                     sun-pale  FEFFD9  pale yellow callout card
steel     3A6783   blue section tint                lime      C8CC3C  lime section tint
success   22C55E   |  danger  EF4444  |  amber  F59E0B   (semantic — only when the data calls for it)
```

Backgrounds vary per slide-type (dark covers, cream content, accent dividers).
Yellow (`sun`/`sun-deep`) is accent only — chips, the left bar, highlights — not
body text and not a full-slide background for text-heavy slides.

### Cards are the backbone

Every content element lives in a rounded-rectangle card. Put the card down
first (no text on it), then layer `add_text` on top. Small consistent radius
(`adjustments[0]` ~0.06-0.18), selective shadow (not every card). This layering
keeps the collision checker happy (cards carry no text).

### Chrome (every slide)

- Left edge: thin `sun` accent bar, full height, ~0.06in wide.
- Top-right: Apollo sunburst mark, auto-picked per background — the Apollo Sun
  (yellow) mark on dark backgrounds, the Stone mark on light/yellow ones.
- Bottom-left: `GTM ENABLEMENT TRAINING` in DM Mono 8pt.
- Bottom-right: page number in DM Mono 8pt.

`add_chrome(slide, bg=..., page_number=...)` does the bar, sunburst mark, and
labels for you. On the cover, set a larger sunburst (e.g. ~0.6in) next to an
"Apollo" wordmark in the display font so the brand reads clearly at least once.

> **Brand mark = the real Apollo sunburst PNG.** `assets/apollo-icon-sun.png`
> (Apollo Sun, for dark backgrounds) and `assets/apollo-icon-stone.png` (Stone,
> for light/yellow backgrounds) are the genuine square, transparent sunburst
> marks. Reach them via `asset_path("icon-sun"|"icon-stone")`. Never approximate
> the sunburst with text glyphs or shapes.

______________________________________________________________________

## SLIDE-TYPE RECIPES (compose freely; these are starting points)

| Slide | Background | Pattern |
|---|---|---|
| Cover | night | Hero title (Space Grotesk 48), date in DM Mono sun, brand mark |
| Agenda | paper | Left numbered rows (chip + title + sub) · right timing sidebar card |
| Section divider | sun or night | Large numbered display title |
| Content | paper | Eyebrow (mono) + title + 2-col: definition card left, labeled rows right |
| Workflow | paper | Numbered card chain with arrow glyphs between steps |
| Evidence (Gong) | paper | Quote card + clip label chips + takeaway |
| Engagement | sun | Big prompt, stone watermark, activity badge |
| Takeaways / CTA | paper | 3-4 numbered cards max |

`scripts/template_deck.py` is a worked example of cover / agenda / two-column
content. Copy it, rename per topic, rewrite the slide bodies — then run it.

______________________________________________________________________

## BUILD FLOW

1. Read `scripts/template_deck.py` for the patterns and helper usage.
1. Write a fresh script under `/tmp/` composing the deck for THIS topic. Import
   constants/helpers from `apollo_brand`; never redefine brand constants.
1. Save to `/tmp/gtme-decks/<topic-slug>.pptx`.
1. The script ends by calling `verify_deck(path)`. If it returns issues, fix the
   offending positions/fonts and rebuild until it returns clean.
1. Confirm: script exited 0, printed `Built deck: <path>`, file is non-empty,
   and `verify_deck` is clean.

## DEFENSES THAT KEEP OUTPUT FUNCTIONAL

- **Fonts:** always one of Space Grotesk / DM Sans / DM Mono (+ the universal
  fallbacks). A stray Calibri/Times means a copy-paste leak — `verify_deck` flags it.
- **Autofit + word_wrap:** `add_text` wraps and shrinks-to-fit by default, so a
  font fallback with different metrics cannot push text out of its box.
- **Card-then-text layering:** never put body text directly on a filled card
  shape's own text frame if it risks colliding with a separate label; use
  separate boxes and keep labels inside card bounds.
- **verify_deck:** the final gate. Off-slide text, >50% text-box collisions, and
  unknown fonts must all be resolved before delivery.

## DO NOT

- Maintain a single generic renderer that stacks full-width textboxes (that was
  the broken version — sparse, colliding, oversized).
- Output a slide spec instead of writing and running the script.
- Ship a deck that `verify_deck` still flags.
- Invent a wordmark or fabricate logo paths — use the bundled PNGs or a simple
  text mark.

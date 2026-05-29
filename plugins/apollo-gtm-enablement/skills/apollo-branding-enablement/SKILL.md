---
name: apollo-branding-enablement
description: Apollo brand toolkit for GTM Enablement PPTX deck production. Activated by apollo-gtm-enablement plugin commands. Use when building or polishing any Apollo-branded GTM Enablement deck. Enforces Apollo Brand Guidelines 2025 — three approved backgrounds (Apollo Sun #FBF500, Stone #252521, Off-White #F9F9F6), SeasonMix Variable / ABC Diatype type stack, three approved icon variants, and visual-first layout rules.
disable-model-invocation: true
---

# Apollo Branding Enablement Skill

Source of truth: Apollo Brand Guidelines 2025

Precedence rule: If older Apollo decks, PDFs, templates, screenshots, or internal references conflict with this skill, this skill wins. Do not reintroduce retired colors, font stacks, or logo treatments from older materials.

**Extended references** (load when you need full specs):

- `references/ui-components.md` — Badge, KPI Card, Timeline, Host Circle, Engagement Activity, etc.
- `references/design-tokens.md` — Spacing grid, shadows, motion presets, glassmorphism, typography fallback tables
- `references/logo-geometry.md` — Canonical SVG paths and React/JSX helper for HTML/web contexts

______________________________________________________________________

## BUNDLED LOGO ASSETS

Use these PNGs for all deck builds. Never approximate the Apollo mark with shapes.

| File | Fill color | Approved background |
|---|---|---|
| `assets/apollo-icon-stone.png` | Stone `#252521` | Off-White `#F9F9F6`, Apollo Sun `#FBF500` |
| `assets/apollo-icon-sun.png` | Apollo Sun `#FBF500` | Stone `#252521` |
| `assets/apollo-icon-white.png` | White | Stone `#252521` |
| `assets/apollo-lockup-stone.png` | Stone `#252521` | Off-White `#F9F9F6`, Apollo Sun `#FBF500` |
| `assets/apollo-lockup-sun.png` | Apollo Sun `#FBF500` symbol + white text | Stone `#252521` |
| `assets/apollo-lockup-white.png` | White | Stone `#252521` |

If a bundled asset cannot be inserted (file missing, permission error), stop and tell the user — do not fake the logo.

______________________________________________________________________

## CORE BRAND TOKENS

```text
Apollo Sun:   #FBF500   <- accent and CTA only. NEVER body text. NEVER a neutral background
Stone:        #252521   <- dark surfaces, primary text, dark slide backgrounds
Off-White:    #F9F9F6   <- light content backgrounds, primary page background
White:        #FFFFFF   <- text on Stone, secondary light support only
```

### Approved Page Backgrounds (only these three)

```text
#FBF500   Apollo Sun    <- high-impact accent pages, engagement slides, CTA covers
#252521   Stone         <- dark covers, section dividers, high-contrast slides
#F9F9F6   Off-White     <- primary content pages, agendas, resource slides
```

No other color is permitted as a page or slide background.

### Logo Pairing Rules

```text
Stone background:      White icon OR Apollo Sun icon
Off-White background:  Stone icon
Apollo Sun background: Stone icon
Never: Apollo Sun icon on Off-White
Never: Stone icon on Stone background
```

______________________________________________________________________

## BANNED. ZERO TOLERANCE

```text
NO  Any page background not in the three approved: #FBF500, #252521, #F9F9F6
NO  Legacy yellows: #F8FF2C, #E8FF00, #FEFF2C, #E1F000
NO  Legacy dark backgrounds: #1A1A1A, #243031, #243332
NO  Legacy cream / sand backgrounds: #F2F0EB, #F3F0EE, #C6C3C0
NO  Retired deck-specific colors: #C8CC3C, #C9C6D3, #DCDDAD
NO  Yellow text on any background (Apollo Sun or any yellow hue) — call assert_text_color()
NO  Orange, coral, amber, purple, teal, or non-core colors
NO  Radial or decorative gradients on slide backgrounds
NO  Flat cards. Every card needs at least --shadow-1
NO  Em-dashes U+2014. Use a period, colon, or parentheses
NO  Emoji in decks, dashboards, or deliverables
NO  Fabricated wordmark lockups or logo paths
NO  Off-scale font sizes. Only 12 / 14 / 16 / 20 / 24 / 32 / 48 / 64 / 96px
NO  Off-spec radii. Only 8 / 12 / 24px
NO  Generated real faces or headshots. Use placeholder circles only
NO  Sunburst as an inline paragraph or button icon
```

______________________________________________________________________

## STEP 0: COLLECT MISSING INPUTS FOR NET-NEW DECKS

Before building a new deck, confirm the following if not already provided:

1. Session title
1. Date
1. Host(s)
1. Learning objectives
1. Agenda / section topics

If any are missing: > Before I build the deck, I need a few things: session title, date, host name(s) and title(s), your learning objectives, and the agenda topics or sections.

If the user explicitly authorizes assumptions, proceed but label which fields were assumed.

______________________________________________________________________

## STEP 1: WRITE A FRESH BUILD SCRIPT PER DECK

For every deck, **write a fresh Python script** that uses `python-pptx` to compose the deck slide-by-slide, then execute it. Each deck is a new design problem; the build script is the design.

### Required imports — the brand toolkit

```python
from apollo_brand import (
    COLORS,            # {"sun": RGBColor, "stone": RGBColor, "off-white": RGBColor, "white": RGBColor}
    TEXT_FOR_BG,       # body-text color per background
    FONT_DISPLAY,      # "SeasonMix Variable"
    FONT_BODY,         # "ABC Diatype"
    SLIDE_W, SLIDE_H,  # 16:9 widescreen dimensions
    asset_path,        # asset_path("icon-white") -> Path to bundled PNG
    set_background,    # set_background(slide, "stone")
    add_chrome,        # add_chrome(slide, bg="stone", page_number=1)
    add_speaker_notes, # add_speaker_notes(slide, "Notes...")
    validate_text,     # validate_text("...") -> list of brand violations
    check_font_size,   # check_font_size(24)  raises if off-scale
    assert_text_color, # assert_text_color(color)  raises if yellow
)
```

### The build flow

1. Read `template_deck.py` (sibling file) as a minimal working starter.
1. Write a new script under `/tmp/` that composes the deck for the current topic.
1. Save to `/tmp/gtme-decks/<topic-slug>.pptx`.
1. Run it (`python3 /tmp/your_deck.py`) and verify output before claiming success.

### Layout guidance

The model owns every layout decision per slide. Compose freely — numbered cards, two-column compare/contrast, full-bleed pull quote, three-column resource grid, host cards, agenda with section numbers in Apollo Sun. Load `references/ui-components.md` for exact component specs when needed.

### Brand validation

- Run `validate_text()` on every user-visible string before saving
- Call `assert_text_color(color)` on every `run.font.color.rgb` assignment — raises on yellow
- Use `TEXT_FOR_BG[bg]` (Stone or White) as the default text color per background
- `check_font_size()` raises on off-scale sizes; `set_background()` raises on non-approved backgrounds

### Do not

- Maintain or extend a single generic renderer — write per-deck scripts
- Output a slide spec as a substitute for actually writing and running the script
- Re-define brand constants in the build script — always import from `apollo_brand`

### Verification rule

Confirm both: script exited with status 0 and printed `Built deck: <path>`, and the output file exists and is non-empty.

______________________________________________________________________

## MANDATORY DESIGN RULES

### NEVER

- Use any page background not in the three approved
- Use yellow as text color on any background — call `assert_text_color()` on every font color
- Use any retired legacy color or font outside this skill's typography system
- Invent a wordmark lockup from typed text or fabricate logo SVG paths
- Generate or suggest real faces / headshots
- Use em-dashes or emoji
- Use flat cards without `--shadow-1`
- Invent a semantic / status palette or chart palette without approval

### ALWAYS

- Keep slides visual-first and text-light (max 4 bullets, 3 lines per block, 15 words per line)
- Include three mandatory chrome elements on every slide
- Apply at least `--shadow-1` to every card element
- Snap all spacing to the 4px base grid

______________________________________________________________________

## MANDATORY SLIDE CHROME (Every Slide)

### 1. Top-Right: Apollo Brand Mark

- Stone background: White or Apollo Sun icon
- Off-White background: Stone icon
- Apollo Sun background: Stone icon
- Position: top-right, `24px` from edges, ~`20-24px` size
- Never typeset "Apollo" as a substitute for an official lockup

### 2. Bottom-Left: Session Label

- Text: `GTM ENABLEMENT TRAINING`
- Font: ABC Diatype `700`, all caps, `10-11px`, letter spacing `0.1em` (fallback: Arial Bold)
- Color: matches slide body text color, position: bottom-left, `24px` from edges

### 3. Bottom-Right: Page Number

- Plain integer: `1`, `2`, `3`...
- Font: ABC Diatype `400`, `10-11px` (fallback: Arial)
- Color: matches slide body text color, position: bottom-right, `24px` from edges

______________________________________________________________________

## DEFAULT TRAINING DECK STRUCTURE

| # | Slide Type | Notes |
|---|---|---|
| 1 | Cover / Title | Session title, date, Apollo brand mark |
| 2 | Learning Objective | "What's in it for me?" + "What do they need to know?" |
| 3 | Agenda | Section names + learning objectives in two columns |
| 4 | Your Host(s) | 1-4 hosts; placeholder circles only |
| 5-N | Content Slides | Deep Dive, Weekly Rundown, Timeline, etc. |
| N+1 | Call to Action | 3-4 numbered action items max |
| N+2 | Resources | Up to 6 resource links in 3-column grid |
| N+3 | Survey | Split layout with QR code placeholder |

Engagement Activity slides inserted at appropriate points within content.

______________________________________________________________________

## SLIDE COLOR SYSTEM

| Slide Type | Background | Text | Key Accent |
|---|---|---|---|
| Cover / Title | `#252521` Stone | `#FFFFFF` | `#FBF500` logo + date label |
| Learning Objective | `#F9F9F6` Off-White | `#252521` | `#FBF500` arrows / labels |
| Agenda | `#F9F9F6` Off-White | `#252521` | `#FBF500` section numbers |
| Your Host(s) | `#252521` Stone | `#FFFFFF` | White names + titles |
| Call to Action | `#F9F9F6` Off-White | `#252521` | `#FBF500` numbered circles |
| Deep Dive / Content | `#F9F9F6` Off-White | `#252521` | `#FBF500` callout border |
| Timeline | `#F9F9F6` Off-White | `#252521` | `#FBF500` milestone nodes |
| Engagement Activity | `#FBF500` Apollo Sun | `#252521` | Stone watermark outline |
| Resources | `#F9F9F6` Off-White | `#252521` | Stone link text |
| Survey / QR | Left `#252521` / Right `#F9F9F6` | Matched | Split layout |

______________________________________________________________________

## TYPOGRAPHY

| Role | Licensed | Fallback | Weight | Use |
|---|---|---|---|---|
| Hero / Display / Headings | SeasonMix Variable | Georgia | 550 | Cover, section titles, H1-H3 |
| Body / UI | ABC Diatype | Helvetica Neue, Arial | 400 | Body copy, bullets, tables |
| Labels / Badges / Footers | ABC Diatype | Arial | 700 | All caps only, letter-spacing 0.1em |

### Type Scale

```text
Cover headline:   72-96px   SeasonMix Variable 550   White on Stone
Section title:    48-64px   SeasonMix Variable 550   Stone on Off-White
Slide title:      28-32px   SeasonMix Variable 550
Body text:        16px      ABC Diatype 400           MINIMUM
Supporting text:  14px      ABC Diatype 400
Badge / label:    12px      ABC Diatype 700 All-Caps
Footer:           12px      ABC Diatype 400 All-Caps
```

Permitted sizes only: `12 / 14 / 16 / 20 / 24 / 32 / 48 / 64 / 96px`

Every text element in a python-pptx build must explicitly set `font.name` — never leave it unset.

See `references/design-tokens.md` for fallback size mapping and letter spacing details.

______________________________________________________________________

## FINAL QA CHECKLIST

Before delivering any deck:

- Only approved backgrounds used
- No yellow text anywhere — `assert_text_color()` called on all font color assignments
- Typography uses SeasonMix / ABC Diatype or approved fallbacks
- Slide chrome uses correct icon pairing per background
- No invented wordmark lockup or fabricated logo paths
- No retired colors present
- No extra palette or semantic colors invented
- Cards use approved radius (8 / 12 / 24px) and shadow rules
- Spacing follows the 4px grid
- Script exited status 0, output file is non-empty

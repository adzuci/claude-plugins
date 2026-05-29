"""Apollo brand toolkit for python-pptx deck builds.

This module exposes the Apollo brand constants and a few small helpers so
build scripts written per-deck don't have to re-encode colors, font names,
asset paths, or banned-content checks. Layout decisions are intentionally
NOT in here — those are the deck author's job per Scott's design system.

Usage from a build script:

    from apollo_brand import COLORS, FONT_BODY, FONT_DISPLAY, asset_path,
                             add_chrome, set_background, validate_text

    deck = Presentation()
    deck.slide_width = SLIDE_W
    deck.slide_height = SLIDE_H

    slide = deck.slides.add_slide(deck.slide_layouts[6])
    set_background(slide, "stone")
    add_chrome(slide, bg="stone", page_number=1)
    # ... add your shapes/text using COLORS, FONT_*, etc.

    deck.save("/tmp/gtme-decks/my-deck.pptx")

When Apollo's brand spec changes, update only this file. See the
sibling SKILL.md for the full design system.
"""
from __future__ import annotations

import re
from pathlib import Path

from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# ---------------------------------------------------------------------------
# Brand constants
# ---------------------------------------------------------------------------

# Apollo's three core tokens (Scott's brand spec)
COLORS = {
    "sun": RGBColor(0xFB, 0xF5, 0x00),
    "stone": RGBColor(0x25, 0x25, 0x21),
    "off-white": RGBColor(0xF9, 0xF9, 0xF6),
    "white": RGBColor(0xFF, 0xFF, 0xFF),
}

# Body text color per slide background (per Scott's slide color system)
TEXT_FOR_BG = {
    "stone": COLORS["white"],
    "sun": COLORS["stone"],
    "off-white": COLORS["stone"],
}

# Icon variant to use for each background (per mandatory chrome rules)
ICON_FOR_BG = {
    "stone": "icon-white",
    "sun": "icon-stone",
    "off-white": "icon-stone",
}

# Typography (falls back if viewer's machine doesn't have the licensed fonts)
FONT_DISPLAY = "SeasonMix Variable"
FONT_BODY = "ABC Diatype"

# Allowed font scale per Scott's "Off-scale font sizes" ban (in points)
FONT_SCALE_PT = {12, 14, 16, 20, 24, 32, 48, 64, 96}

# Allowed border radii per Scott's spec (in points; convert to EMU at use)
ALLOWED_RADII_PT = {8, 12, 24}

# Slide dimensions (16:9 widescreen)
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# Default session label (override per deck if needed)
DEFAULT_SESSION_LABEL = "GTM ENABLEMENT TRAINING"

# Chrome positioning (24px from edges per Scott's spec; ~0.24in at slide DPI)
CHROME_MARGIN_IN = 0.24
CHROME_FONT_PT = 12  # closest allowed scale point to the 10-11pt spec

# Asset directory (PNGs live in sibling assets/ folder)
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"

# Approved backgrounds — anything else should fail validation
VALID_BACKGROUNDS = {"stone", "sun", "off-white"}


# ---------------------------------------------------------------------------
# Banned content per Scott's "BANNED. ZERO TOLERANCE" section
# ---------------------------------------------------------------------------

BANNED_CHARS = {"—": "em-dash (U+2014); use a period, colon, or parentheses"}

EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"
    "\U0001f300-\U0001f5ff"
    "\U0001f680-\U0001f6ff"
    "\U0001f1e0-\U0001f1ff"
    "\U00002700-\U000027bf"
    "\U0001f900-\U0001f9ff"
    "]+"
)

LEGACY_COLOR_TOKENS = frozenset({
    "#F8FF2C", "#E8FF00", "#FEFF2C", "#E1F000",  # legacy yellows
    "#1A1A1A", "#243031", "#243332",  # legacy darks
    "#F2F0EB", "#F3F0EE", "#C6C3C0",  # legacy creams
    "#C8CC3C", "#C9C6D3", "#DCDDAD",  # retired
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def asset_path(name: str) -> Path:
    """Return the absolute path of a bundled logo asset.

    `name` is the variant slug without extension, e.g. "icon-white", "lockup-sun".
    Raises FileNotFoundError if the asset doesn't exist.
    """
    candidate = ASSET_DIR / f"apollo-{name}.png"
    if not candidate.is_file():
        raise FileNotFoundError(
            f"Apollo logo asset not found: {candidate}. "
            f"Available: {sorted(p.name for p in ASSET_DIR.glob('apollo-*.png'))}"
        )
    return candidate


def validate_text(text: str) -> list[str]:
    """Run brand-compliance checks on a single text string.

    Returns a list of error messages (empty if the text passes). Call this
    on every user-visible string in the deck before saving.
    """
    errors: list[str] = []
    for char, msg in BANNED_CHARS.items():
        if char in text:
            errors.append(f"text contains banned {msg}: {text!r}")
    if EMOJI_PATTERN.search(text):
        errors.append(f"text contains emoji (banned per brand rules): {text!r}")
    for legacy in LEGACY_COLOR_TOKENS:
        if legacy.lower() in text.lower():
            errors.append(f"text references legacy color {legacy}: {text!r}")
    return errors


def set_background(slide, bg: str) -> None:
    """Fill the slide background with the named brand color.

    `bg` must be one of VALID_BACKGROUNDS.
    """
    if bg not in VALID_BACKGROUNDS:
        raise ValueError(
            f"bg {bg!r} is not approved. Use one of {sorted(VALID_BACKGROUNDS)}."
        )
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = COLORS[bg]


def add_chrome(
    slide,
    *,
    bg: str,
    page_number: int,
    session_label: str = DEFAULT_SESSION_LABEL,
) -> None:
    """Add the three mandatory chrome elements per Scott's brand spec.

    1. Top-right: Apollo brand icon (variant picked by bg per ICON_FOR_BG)
    2. Bottom-left: session label (e.g. "GTM ENABLEMENT TRAINING")
    3. Bottom-right: page number
    """
    text_color = TEXT_FOR_BG[bg]
    margin = Inches(CHROME_MARGIN_IN)
    icon_size = Inches(0.32)

    # Top-right brand icon
    slide.shapes.add_picture(
        str(asset_path(ICON_FOR_BG[bg])),
        SLIDE_W - icon_size - margin,
        margin,
        width=icon_size,
        height=icon_size,
    )

    # Bottom-left session label
    label_box = slide.shapes.add_textbox(
        margin, SLIDE_H - Inches(CHROME_MARGIN_IN + 0.2),
        Inches(4), Inches(0.2),
    )
    p = label_box.text_frame.paragraphs[0]
    run = p.add_run()
    run.text = session_label
    run.font.name = FONT_BODY
    run.font.size = Pt(CHROME_FONT_PT)
    run.font.bold = True
    run.font.color.rgb = text_color

    # Bottom-right page number
    page_box = slide.shapes.add_textbox(
        SLIDE_W - Inches(CHROME_MARGIN_IN + 0.5),
        SLIDE_H - Inches(CHROME_MARGIN_IN + 0.2),
        Inches(0.5), Inches(0.2),
    )
    p = page_box.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    run = p.add_run()
    run.text = str(page_number)
    run.font.name = FONT_BODY
    run.font.size = Pt(CHROME_FONT_PT)
    run.font.color.rgb = text_color


def add_speaker_notes(slide, text: str) -> None:
    """Attach speaker notes to a slide. No-op if text is empty."""
    if not text:
        return
    slide.notes_slide.notes_text_frame.text = text


def check_font_size(pt: int) -> None:
    """Raise if pt is not in Apollo's allowed font scale."""
    if pt not in FONT_SCALE_PT:
        raise ValueError(
            f"font size {pt}pt is off-scale. Allowed: {sorted(FONT_SCALE_PT)}"
        )


def assert_text_color(color: RGBColor) -> None:
    """Raise if color is yellow or any yellow-adjacent hue.

    Yellow text is never permitted — it fails contrast on light backgrounds
    and looks unintentional on dark ones. Detection is hue-based so it
    catches any shade of yellow, not just Apollo Sun.
    """
    r, g, b = color[0], color[1], color[2]
    # Convert to 0-1 range
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    max_c = max(rf, gf, bf)
    min_c = min(rf, gf, bf)
    delta = max_c - min_c
    if delta == 0 or max_c == 0:
        return  # achromatic (black/white/gray) — always allowed
    # Hue in [0, 360)
    if max_c == rf:
        hue = 60.0 * (((gf - bf) / delta) % 6)
    elif max_c == gf:
        hue = 60.0 * (((bf - rf) / delta) + 2)
    else:
        hue = 60.0 * (((rf - gf) / delta) + 4)
    # Yellow hues: roughly 45°–75° (narrow band around 60°)
    saturation = delta / max_c
    if saturation > 0.3 and 45 <= hue <= 75:
        raise ValueError(
            f"Yellow text is not permitted (hue={hue:.0f}°, color=#{r:02X}{g:02X}{b:02X}). "
            "Use Stone (#252521) or White (#FFFFFF) for text."
        )

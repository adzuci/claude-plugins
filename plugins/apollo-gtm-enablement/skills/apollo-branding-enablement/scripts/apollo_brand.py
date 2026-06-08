"""Apollo GTME deck toolkit — light helpers + a post-build verifier.

Philosophy: the deck author (the model) owns every layout decision and writes
a fresh python-pptx script per deck. This module does NOT cage that freedom —
there are no validators that reject font sizes, colors, or characters. It only
provides:

  1. Reference constants — the real palette, fonts (with safe fallbacks),
     canvas size, and chrome geometry extracted from the reference decks that
     look good. Use them or override them per deck.
  2. Optional convenience helpers — set_background, add_chrome, add_text,
     add_speaker_notes. Use them or roll your own.
  3. verify_deck(path) — the functional guarantee. Run it AFTER building. It
     catches the glitch class that actually broke past decks: shapes off the
     slide, two text boxes colliding, and fonts that will not render. Fix
     whatever it flags and rebuild.

The functional guarantee lives in verification AFTER the build, not in
restrictions BEFORE it — so design stays free and output stays correct.

Usage from a build script:

    from apollo_brand import (
        PALETTE, FONT_DISPLAY, FONT_BODY, FONT_MONO,
        SLIDE_W, SLIDE_H, set_background, add_chrome, add_text, verify_deck,
    )

    deck = Presentation()
    deck.slide_width = SLIDE_W
    deck.slide_height = SLIDE_H
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    set_background(slide, "night")
    # ... compose freely ...
    add_chrome(slide, bg="night", page_number=1)
    deck.save("/tmp/gtme-decks/my-deck.pptx")

    issues = verify_deck("/tmp/gtme-decks/my-deck.pptx")
    assert not issues, issues

See SKILL.md for the full design reference (palette roles, type scale,
card patterns, slide-type recipes).
"""
from __future__ import annotations

import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Emu, Inches, Pt

# ---------------------------------------------------------------------------
# Canvas — matches the reference decks (16:9 at Google-Slides scale)
# ---------------------------------------------------------------------------

SLIDE_W = Inches(10.0)
SLIDE_H = Inches(5.625)

# ---------------------------------------------------------------------------
# Palette — the working palette from the reference decks, with role names.
# These are the colors the good decks actually use. Pass a role name to the
# helpers, or pass any "RRGGBB" hex string directly — nothing is rejected.
# ---------------------------------------------------------------------------

PALETTE = {
    # text / ink
    "ink": "1A1A1A",        # primary text on light backgrounds
    "white": "FFFFFF",      # text on dark backgrounds
    "muted": "736F6C",      # secondary text
    "muted-2": "94918E",    # tertiary / captions
    "muted-3": "47423D",    # dark muted
    # surfaces (light)
    "paper": "F3F0EE",      # primary light slide background
    "paper-2": "F2F0EB",    # cream variant
    "paper-3": "F7F5F2",    # lightest cream
    # surfaces (dark)
    "night": "243031",      # primary dark slide background / cover
    # accents
    "sun": "F8FF2C",        # primary yellow accent (chips, accent bar, highlights)
    "sun-deep": "E1F000",   # deeper yellow (numbered chips, "done" nodes)
    "sun-pale": "FEFFD9",   # pale yellow callout card
    "mist": "CCC9C6",       # neutral grey card fill
    "lavender": "C9C6D3",   # section tint
    "steel": "3A6783",      # blue section tint
    "lime": "C8CC3C",       # lime section tint
    # semantic (use sparingly, only when the data calls for it)
    "success": "22C55E",
    "danger": "EF4444",
    "amber": "F59E0B",
}

# Default body-text color per common background role
TEXT_ON = {
    "night": "white",
    "steel": "white",
    "ink": "white",
    "paper": "ink",
    "paper-2": "ink",
    "paper-3": "ink",
    "sun": "ink",
    "sun-deep": "ink",
    "sun-pale": "ink",
    "mist": "ink",
    "lavender": "ink",
    "lime": "ink",
}

# ---------------------------------------------------------------------------
# Typography — Google Fonts the reference decks use, each with a metric-close
# fallback so layout survives when the licensed font is not installed on the
# viewer's machine. Always pass these through add_text / set the run font name.
# ---------------------------------------------------------------------------

FONT_DISPLAY = "Space Grotesk"   # titles, hero, section heads. Fallback: Arial
FONT_BODY = "DM Sans"            # body copy, bullets, cards. Fallback: Arial
FONT_MONO = "DM Mono"            # labels, metrics, code, SFDC names. Fallback: Consolas

# Fonts we know render acceptably (licensed Google Fonts + universal fallbacks).
# verify_deck flags anything outside this set so a stray Calibri/Times does not
# silently ship.
KNOWN_FONTS = {
    FONT_DISPLAY, FONT_BODY, FONT_MONO,
    "Arial", "Helvetica", "Helvetica Neue", "Consolas", "Courier New",
}

# Chrome geometry (matches reference decks)
CHROME_MARGIN = Inches(0.35)
ACCENT_BAR_W = Inches(0.06)

# Apollo sunburst mark variant per background: the Apollo Sun (yellow) mark on
# dark backgrounds, the Stone (dark) mark on light/yellow backgrounds. Both are
# the real Apollo sunburst (square, transparent) bundled under assets/.
ICON_FOR_BG = {
    "night": "icon-sun", "steel": "icon-sun", "ink": "icon-sun",
    "paper": "icon-stone", "paper-2": "icon-stone", "paper-3": "icon-stone",
    "sun": "icon-stone", "sun-deep": "icon-stone", "sun-pale": "icon-stone",
    "mist": "icon-stone", "lavender": "icon-stone", "lime": "icon-stone",
}

# Bundled logo assets (PNGs in sibling assets/ folder)
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"


# ---------------------------------------------------------------------------
# Color helper
# ---------------------------------------------------------------------------


def color(name_or_hex: str) -> RGBColor:
    """Resolve a palette role name (e.g. "night") or a raw "RRGGBB" hex string
    to an RGBColor. Raw hex is accepted as-is — no color is rejected."""
    hexval = PALETTE.get(name_or_hex, name_or_hex).lstrip("#")
    return RGBColor.from_string(hexval)


# ---------------------------------------------------------------------------
# Asset helper
# ---------------------------------------------------------------------------


def asset_path(name: str) -> Path:
    """Absolute path of a bundled logo asset, e.g. asset_path("icon-white").
    Raises FileNotFoundError if missing — never fake the logo."""
    candidate = ASSET_DIR / f"apollo-{name}.png"
    if not candidate.is_file():
        raise FileNotFoundError(
            f"Apollo logo asset not found: {candidate}. "
            f"Available: {sorted(p.name for p in ASSET_DIR.glob('apollo-*.png'))}"
        )
    return candidate


# ---------------------------------------------------------------------------
# Optional convenience helpers — use them or compose shapes yourself
# ---------------------------------------------------------------------------


def set_background(slide, bg: str) -> None:
    """Fill the slide background with a palette role or raw hex. Anything goes."""
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color(bg)


def add_text(
    slide,
    text,
    *,
    left,
    top,
    width,
    height,
    size,
    font=FONT_BODY,
    fill="ink",
    bold=False,
    align=PP_ALIGN.LEFT,
    autosize=True,
    wrap=True,
):
    """Add a text box. By default word-wraps and shrinks text to fit its box,
    so a font fallback (different metrics) cannot push text out of the box.
    This is the main defense against the collision/overflow glitch class."""
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = wrap
    if autosize:
        tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color(fill)
    return box


def add_chrome(slide, *, bg: str, page_number: int, session_label: str = "GTM ENABLEMENT TRAINING") -> None:
    """Add the four reference chrome elements: left edge yellow accent bar,
    top-right Apollo sunburst mark, bottom-left session label, bottom-right
    page number.

    The brand mark is the real Apollo sunburst PNG (square, transparent),
    auto-picked per background: the Apollo Sun (yellow) mark on dark
    backgrounds, the Stone mark on light/yellow ones."""
    text_color = TEXT_ON.get(bg, "ink")

    # Left-edge accent bar
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Emu(0), Emu(0), ACCENT_BAR_W, SLIDE_H,
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = color("sun")
    bar.line.fill.background()
    bar.shadow.inherit = False

    # Top-right Apollo sunburst mark (square asset → square box, no distortion)
    mark = Inches(0.32)
    slide.shapes.add_picture(
        str(asset_path(ICON_FOR_BG.get(bg, "icon-stone"))),
        SLIDE_W - mark - CHROME_MARGIN, CHROME_MARGIN - Inches(0.04),
        width=mark, height=mark,
    )

    add_text(
        slide, session_label,
        left=CHROME_MARGIN, top=SLIDE_H - Inches(0.30),
        width=Inches(4.0), height=Inches(0.2),
        size=8, font=FONT_MONO, fill=text_color, autosize=False,
    )
    add_text(
        slide, str(page_number),
        left=SLIDE_W - Inches(0.6), top=SLIDE_H - Inches(0.30),
        width=Inches(0.4), height=Inches(0.2),
        size=8, font=FONT_MONO, fill=text_color, align=PP_ALIGN.RIGHT, autosize=False,
    )


def add_speaker_notes(slide, text: str) -> None:
    """Attach speaker notes. No-op on empty text."""
    if text:
        slide.notes_slide.notes_text_frame.text = text


# ---------------------------------------------------------------------------
# verify_deck — the functional guarantee (run AFTER building)
# ---------------------------------------------------------------------------

_TOL = Pt(2)  # geometry tolerance in EMU (~2pt)


def _bbox(shape):
    if None in (shape.left, shape.top, shape.width, shape.height):
        return None
    return (shape.left, shape.top, shape.left + shape.width, shape.top + shape.height)


def _overlap_area(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return ix * iy


def verify_deck(path: str) -> list[str]:
    """Geometric + font sanity check on a built deck. Returns a list of issue
    strings (empty == deck is functionally sound).

    Catches the glitch class that actually broke past decks:
      - shapes positioned off the slide edges
      - two text-bearing boxes colliding (text-on-text collision)
      - fonts that will not render on a normal machine

    It is layout-agnostic: it does not judge design, only whether the file
    will render without artifacts. Layered card-behind-text is fine (the card
    carries no text); only two real text boxes overlapping is flagged."""
    prs = Presentation(path)
    sw, sh = prs.slide_width, prs.slide_height
    issues: list[str] = []

    for si, slide in enumerate(list(prs.slides), start=1):
        text_boxes = []
        for shape in slide.shapes:
            box = _bbox(shape)
            if box is None:
                continue
            has_text = shape.has_text_frame and shape.text_frame.text.strip()
            # off-slide check — only for text (decorative full-bleed shapes and
            # images are placed off-edge on purpose; text running off is a bug)
            if has_text and (box[0] < -_TOL or box[1] < -_TOL
                             or box[2] > sw + _TOL or box[3] > sh + _TOL):
                issues.append(
                    f"slide {si}: text off-slide ({shape.text_frame.text[:30]!r}) "
                    f"bounds exceed canvas"
                )
            # collect non-empty text boxes for collision check
            if has_text:
                text_boxes.append((box, shape.text_frame.text[:30]))
                # font check
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        fn = run.font.name
                        if fn and fn not in KNOWN_FONTS:
                            issues.append(
                                f"slide {si}: unknown font {fn!r} (will fall back; "
                                f"use {FONT_DISPLAY}/{FONT_BODY}/{FONT_MONO})"
                            )

        # text-on-text collision check. Two non-empty text boxes overlapping by
        # >50% of the smaller box is a collision — including the nested/equal
        # case (a box sitting inside a larger text box), which is still text on
        # text. Card-behind-text never trips this: a filled card carries no text
        # so it is not in text_boxes.
        for i in range(len(text_boxes)):
            for j in range(i + 1, len(text_boxes)):
                a, b = text_boxes[i][0], text_boxes[j][0]
                area = _overlap_area(a, b)
                if area <= 0:
                    continue
                smaller = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
                if smaller > 0 and area / smaller > 0.5:
                    issues.append(
                        f"slide {si}: text collision between {text_boxes[i][1]!r} "
                        f"and {text_boxes[j][1]!r} ({area / smaller:.0%} overlap)"
                    )

    # de-dup while preserving order
    seen = set()
    deduped = []
    for it in issues:
        if it not in seen:
            seen.add(it)
            deduped.append(it)
    return deduped


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "verify":
        found = verify_deck(sys.argv[2])
        if found:
            print(f"verify_deck: {len(found)} issue(s) in {sys.argv[2]}")
            for it in found:
                print(f"  - {it}")
            sys.exit(1)
        print(f"verify_deck: OK — {sys.argv[2]} is functionally sound")
    else:
        print("usage: python apollo_brand.py verify <deck.pptx>")
        sys.exit(2)

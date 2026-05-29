"""Starter template for an Apollo GTM Enablement deck.

Copy this file, rename it for your topic (e.g. `outbound_cadence.py`),
edit the slide functions, and run:

    python3 outbound_cadence.py

The model is expected to write a fresh script PER DECK, owning layout
decisions per slide. Brand constants and chrome live in apollo_brand;
do NOT redefine them here.

Reference docs:
- ../SKILL.md          Full design system (colors, fonts, layouts, banned items)
- apollo_brand.py      Brand toolkit (constants, asset paths, helpers)
"""
from __future__ import annotations

import sys
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# When this script is generated and run from /tmp/, the toolkit lives next
# to the SKILL.md; resolve via the apollo-branding-enablement skill folder.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from apollo_brand import (  # noqa: E402
    COLORS,
    FONT_BODY,
    FONT_DISPLAY,
    SLIDE_H,
    SLIDE_W,
    TEXT_FOR_BG,
    add_chrome,
    add_speaker_notes,
    asset_path,
    check_font_size,
    set_background,
    validate_text,
)

# ---------------------------------------------------------------------------
# Edit this metadata per deck
# ---------------------------------------------------------------------------

DECK_TITLE = "Session Title Here"
DECK_DATE = "2026-MM-DD"
HOSTS = [{"name": "First Last", "title": "Role"}]
OUTPUT_PATH = Path("/tmp/gtme-decks/example.pptx")


# ---------------------------------------------------------------------------
# Helpers that wrap python-pptx for brand-safe text adds
# ---------------------------------------------------------------------------


def add_text(slide, text, *, left, top, width, height, size, font, color, bold=False, align=PP_ALIGN.LEFT):
    check_font_size(size)
    errors = validate_text(text)
    if errors:
        raise ValueError("\n".join(errors))
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


# ---------------------------------------------------------------------------
# Slide-by-slide layout — author owns these decisions
# ---------------------------------------------------------------------------


def add_title_slide(deck, page):
    """Cover slide. Stone bg, display title, hosts + date as accent line."""
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    bg = "stone"
    set_background(slide, bg)
    text_color = TEXT_FOR_BG[bg]

    add_text(
        slide, DECK_TITLE,
        left=Inches(0.8), top=Inches(2.8), width=Inches(11), height=Inches(1.6),
        size=64, font=FONT_DISPLAY, color=text_color, bold=True,
    )

    host_line = "  ·  ".join(f"{h['name']}, {h['title']}" for h in HOSTS)
    add_text(
        slide, f"{DECK_DATE}  ·  {host_line}",
        left=Inches(0.8), top=Inches(4.8), width=Inches(11), height=Inches(0.5),
        size=20, font=FONT_BODY, color=COLORS["sun"],
    )

    add_chrome(slide, bg=bg, page_number=page)
    add_speaker_notes(slide, "Welcome the team. Remind them this is recorded.")


def add_section_divider(deck, page, *, number, title):
    """Section divider. Apollo Sun bg, large display title."""
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    bg = "sun"
    set_background(slide, bg)

    add_text(
        slide, f"{number}. {title}",
        left=Inches(0.8), top=Inches(3.0), width=Inches(11), height=Inches(1.6),
        size=64, font=FONT_DISPLAY, color=TEXT_FOR_BG[bg], bold=True,
    )

    add_chrome(slide, bg=bg, page_number=page)


def add_content_slide(deck, page, *, title, paragraphs=(), bullets=()):
    """Generic content slide. Off-white bg, title at top, content stacked."""
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    bg = "off-white"
    set_background(slide, bg)
    text_color = TEXT_FOR_BG[bg]

    add_text(
        slide, title,
        left=Inches(0.8), top=Inches(0.8), width=Inches(11.5), height=Inches(1.0),
        size=48, font=FONT_DISPLAY, color=text_color, bold=True,
    )

    top_in = 2.0
    for p in paragraphs:
        add_text(
            slide, p,
            left=Inches(0.8), top=Inches(top_in), width=Inches(11.5), height=Inches(1.2),
            size=24, font=FONT_BODY, color=text_color,
        )
        top_in += 1.4

    if bullets:
        # Compose all bullets in a single textbox so spacing is consistent
        box = slide.shapes.add_textbox(
            Inches(0.8), Inches(top_in), Inches(11.5), Inches(0.6 * len(bullets) + 0.4)
        )
        tf = box.text_frame
        tf.word_wrap = True
        for idx, item in enumerate(bullets):
            errors = validate_text(item)
            if errors:
                raise ValueError("\n".join(errors))
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            run = p.add_run()
            run.text = f"• {item}"
            run.font.name = FONT_BODY
            run.font.size = Pt(24)
            run.font.color.rgb = text_color

    add_chrome(slide, bg=bg, page_number=page)


# ---------------------------------------------------------------------------
# Compose the deck — model edits this body per deck
# ---------------------------------------------------------------------------


def build() -> Path:
    deck = Presentation()
    deck.slide_width = SLIDE_W
    deck.slide_height = SLIDE_H

    add_title_slide(deck, page=1)
    add_section_divider(deck, page=2, number=1, title="Why this matters")
    add_content_slide(
        deck, page=3,
        title="The data",
        paragraphs=["Replace this with the substance of the slide."],
        bullets=["Point one", "Point two", "Point three"],
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    deck.save(str(OUTPUT_PATH))
    return OUTPUT_PATH


if __name__ == "__main__":
    path = build()
    print(f"Built deck: {path}")

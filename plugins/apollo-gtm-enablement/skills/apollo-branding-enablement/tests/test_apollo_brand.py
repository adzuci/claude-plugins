"""Tests for the apollo_brand toolkit.

Run from the repo root:
    pip install -r plugins/apollo-gtm-enablement/skills/apollo-branding-enablement/tests/requirements.txt
    python -m pytest -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("pptx")

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import apollo_brand  # noqa: E402


# ---- asset_path ----


def test_asset_path_resolves_existing_logo():
    p = apollo_brand.asset_path("icon-white")
    assert p.is_file()
    assert p.name == "apollo-icon-white.png"


def test_asset_path_resolves_all_known_variants():
    for variant in (
        "icon-white", "icon-stone", "icon-sun",
        "lockup-white", "lockup-stone", "lockup-sun",
    ):
        assert apollo_brand.asset_path(variant).is_file()


def test_asset_path_raises_for_unknown_variant():
    with pytest.raises(FileNotFoundError):
        apollo_brand.asset_path("icon-purple")


# ---- validate_text ----


def test_validate_text_passes_clean_string():
    assert apollo_brand.validate_text("This is a normal sentence.") == []


def test_validate_text_flags_em_dash():
    errors = apollo_brand.validate_text("Apollo — the revenue engine")
    assert any("em-dash" in e for e in errors)


def test_validate_text_flags_emoji():
    errors = apollo_brand.validate_text("Apollo is fast 🚀")
    assert any("emoji" in e for e in errors)


def test_validate_text_flags_legacy_color():
    errors = apollo_brand.validate_text("Background should be #1A1A1A.")
    assert any("#1A1A1A" in e for e in errors)


def test_validate_text_flags_legacy_color_case_insensitively():
    errors = apollo_brand.validate_text("Background should be #1a1a1a.")
    assert any("#1A1A1A" in e for e in errors)


# ---- set_background ----


def test_set_background_rejects_invalid_color():
    class FakeSlide:
        class background:
            class fill:
                @staticmethod
                def solid():
                    pass

    with pytest.raises(ValueError, match="orange"):
        apollo_brand.set_background(FakeSlide(), "orange")


# ---- check_font_size ----


def test_check_font_size_allows_in_scale():
    for pt in (12, 14, 16, 20, 24, 32, 48, 64, 96):
        apollo_brand.check_font_size(pt)  # no raise


def test_check_font_size_rejects_off_scale():
    with pytest.raises(ValueError, match="off-scale"):
        apollo_brand.check_font_size(18)


# ---- assert_text_color ----


def test_assert_text_color_allows_white():
    apollo_brand.assert_text_color(apollo_brand.RGBColor(0xFF, 0xFF, 0xFF))


def test_assert_text_color_allows_stone():
    apollo_brand.assert_text_color(apollo_brand.RGBColor(0x25, 0x25, 0x21))


def test_assert_text_color_rejects_apollo_sun():
    with pytest.raises(ValueError, match="Yellow text"):
        apollo_brand.assert_text_color(apollo_brand.RGBColor(0xFB, 0xF5, 0x00))


def test_assert_text_color_rejects_any_yellow():
    # A generic bright yellow not in the brand palette
    with pytest.raises(ValueError, match="Yellow text"):
        apollo_brand.assert_text_color(apollo_brand.RGBColor(0xFF, 0xFF, 0x00))


def test_assert_text_color_allows_mid_blue():
    # Blue should never be flagged as yellow
    apollo_brand.assert_text_color(apollo_brand.RGBColor(0x00, 0x80, 0xFF))


# ---- end-to-end smoke test using the toolkit ----


def test_can_build_minimal_deck_with_toolkit(tmp_path):
    """Compose a one-slide deck using only toolkit primitives to confirm
    they cooperate with python-pptx end-to-end."""
    from pptx import Presentation

    deck = Presentation()
    deck.slide_width = apollo_brand.SLIDE_W
    deck.slide_height = apollo_brand.SLIDE_H

    slide = deck.slides.add_slide(deck.slide_layouts[6])
    apollo_brand.set_background(slide, "stone")
    apollo_brand.add_chrome(slide, bg="stone", page_number=1)
    apollo_brand.add_speaker_notes(slide, "Test notes")

    out = tmp_path / "smoke.pptx"
    deck.save(str(out))
    assert out.exists() and out.stat().st_size > 0

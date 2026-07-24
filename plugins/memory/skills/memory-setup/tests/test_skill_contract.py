"""Contract checks for the user-facing memory-setup flow."""

from pathlib import Path


SKILL = Path(__file__).resolve().parent.parent / "SKILL.md"


def test_setup_contract_covers_apollo_personal_sync_and_obsidian() -> None:
    text = SKILL.read_text()

    assert "apolloio/<name>-vault" in text
    assert "Personal private repository" in text
    assert "--interval 900" in text
    assert "open -a Obsidian" in text
    assert "Open folder as vault" in text
    assert "README.md" in text

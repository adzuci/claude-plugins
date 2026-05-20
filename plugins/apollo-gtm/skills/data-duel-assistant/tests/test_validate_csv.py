import pytest

validate_csv = pytest.importorskip("validate_csv")


@pytest.mark.parametrize("raw,expected", [
    ("Organization Name", "organization_name"),
    ("first-name", "first_name"),
    ("  EMAIL  ", "email"),
])
def test_normalize_col(raw, expected):
    assert validate_csv.normalize_col(raw) == expected


def test_match_column_direct_model_hit():
    model_col, note = validate_csv.match_column("organization_name")
    assert model_col == "organization_name"
    assert note is None


def test_match_column_alias():
    model_col, note = validate_csv.match_column("Company")
    assert model_col == "organization_name"
    assert note and "Alias" in note


def test_match_column_split_full_name():
    model_col, _ = validate_csv.match_column("Full Name")
    assert model_col == "SPLIT:first_name,last_name"


def test_match_column_unknown():
    model_col, note = validate_csv.match_column("totally_custom_field_xyz")
    assert model_col is None
    assert note is None

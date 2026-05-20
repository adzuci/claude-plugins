import pytest

generate_output = pytest.importorskip("generate_output")


def test_safe_json_valid():
    assert generate_output.safe_json('{"a": 1}') == {"a": 1}


@pytest.mark.parametrize("v", ["", "{}", "null", "not json", None])
def test_safe_json_falls_back_to_empty(v):
    assert generate_output.safe_json(v) == {}


@pytest.mark.parametrize("v,expected", [
    ("apollo", "apollo"),
    ("  apollo  ", "apollo"),
    ("#N/A", None),
    ("null", None),
    ("", None),
    (None, None),
])
def test_nv_normalizes_junk(v, expected):
    assert generate_output.nv(v) == expected


def test_coalesce_returns_first_non_junk():
    assert generate_output.coalesce(None, "#N/A", "apollo", "fallback") == "apollo"
    assert generate_output.coalesce(None, "null", "") is None


def test_find_vendor_col():
    cols = ["row_id", "apollo_response", "Prospeo_JSON", "limadata"]
    assert generate_output.find_vendor_col(cols, "apollo") == "apollo_response"
    assert generate_output.find_vendor_col(cols, "prospeo") == "Prospeo_JSON"
    assert generate_output.find_vendor_col(cols, "missing") is None


def test_from_apollo_extracts_org_phone_and_employer():
    payload = {
        "title": "VP Sales",
        "seniority": "vp",
        "organization": {"phone": "+1-555-0100", "name": "Acme"},
    }
    out = generate_output.from_apollo(payload)
    assert out["matched"] is True
    assert out["title"] == "VP Sales"
    assert out["phone"] == "+1-555-0100"
    assert out["current_employer"] == "Acme"


def test_from_apollo_skips_errors():
    assert generate_output.from_apollo({"error": "rate_limited"}) == {}
    assert generate_output.from_apollo({}) == {}


def test_from_prospeo_only_emits_verified_email():
    verified = {"person": {"email": {"email": "a@b.com", "status": "VERIFIED"}}}
    unverified = {"person": {"email": {"email": "a@b.com", "status": "UNKNOWN"}}}
    assert generate_output.from_prospeo(verified)["email"] == "a@b.com"
    assert generate_output.from_prospeo(unverified)["email"] is None

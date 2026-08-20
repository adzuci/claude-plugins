from __future__ import annotations

import pytest

ids = pytest.importorskip("check_id_formats")


# --- Mongo ObjectId ---------------------------------------------------------


def test_valid_objectid_accepted():
    assert ids.is_object_id("694375d2ea31700011157c39")
    assert ids.is_object_id("609b0aa91be27700a4ecd015")


def test_objectid_rejects_non_hex():
    # The 2026-08-10 tabletop sample used 66ttx... — t and x are not hex.
    assert not ids.is_object_id("66ttx000000000000000027")
    assert not ids.is_object_id("66ttx0000000000000000001")


def test_objectid_rejects_wrong_length():
    assert not ids.is_object_id("694375d2ea31700011157c3")
    assert not ids.is_object_id("694375d2ea31700011157c390")


def test_objectid_rejects_uppercase_hex():
    assert not ids.is_object_id("694375D2EA31700011157C39")


def test_objectid_timestamp_decodes_epoch():
    epoch = ids.object_id_timestamp("00000000" + "0" * 16)
    assert epoch.year == 1970 and epoch.month == 1 and epoch.day == 1


def test_objectid_timestamp_is_plausible_for_real_id():
    stamp = ids.object_id_timestamp("694375d2ea31700011157c39")
    assert 2020 <= stamp.year <= 2100


def test_objectid_timestamp_returns_none_for_invalid():
    assert ids.object_id_timestamp("not-an-object-id") is None


# --- Salesforce -------------------------------------------------------------


def test_salesforce_suffix_all_digits_is_aaa():
    # No uppercase letters anywhere -> every 5-bit chunk is 0 -> "AAA".
    assert ids.salesforce_suffix("001000000000000") == "AAA"


def test_salesforce_suffix_all_uppercase_is_555():
    # Every chunk is 0b11111 = 31 -> index 31 of the alphabet -> "5".
    assert ids.salesforce_suffix("ABCDEABCDEABCDE") == "555"


def test_salesforce_suffix_bit_order_is_least_significant_first():
    assert ids.salesforce_suffix("A0000" + "0" * 10) == "BAA"
    assert ids.salesforce_suffix("0000A" + "0" * 10) == "QAA"


def test_salesforce_suffix_ignores_lowercase():
    assert ids.salesforce_suffix("a0000" + "0" * 10) == "AAA"


def test_valid_15_and_18_char_ids_accepted():
    fifteen = "001000000000000"
    assert ids.is_salesforce_id(fifteen)
    assert ids.is_salesforce_id(fifteen + ids.salesforce_suffix(fifteen))


def test_18_char_id_with_bad_checksum_rejected():
    fifteen = "001000000000000"
    assert not ids.is_salesforce_id(fifteen + "ZZZ")


def test_salesforce_prefix_must_match_claimed_entity():
    # 001 is Account. Claiming it is a Contact record is a mismatch.
    assert ids.salesforce_entity("001000000000000") == "Account"
    assert ids.prefix_matches("001000000000000", "Account")
    assert not ids.prefix_matches("001000000000000", "Contact")


def test_unknown_prefix_reports_none():
    assert ids.salesforce_entity("ZZZ000000000000") is None


def test_synthetic_prefixed_ids_are_not_salesforce():
    # The tabletop sample used sf_0270000001 / cnt_027_0000001 / per_0027000001.
    for value in ("sf_0270000001", "cnt_027_0000001", "per_0027000001"):
        assert not ids.is_salesforce_id(value)
        assert not ids.is_object_id(value)


# --- Cross-column ordinal correlation ---------------------------------------


def test_ordinal_correlation_detects_lockstep_columns():
    rows = [
        {"team": "66ttx0000000000000000001", "sfdc": "001TTX000000001"},
        {"team": "66ttx0000000000000000002", "sfdc": "001TTX000000002"},
        {"team": "66ttx0000000000000000003", "sfdc": "001TTX000000003"},
    ]
    result = ids.ordinal_correlation(rows, "team", "sfdc")
    assert result["compared"] == 3
    assert result["matching"] == 3
    assert result["correlated"] is True


def test_ordinal_correlation_clears_independent_columns():
    rows = [
        {"team": "694375d2ea31700011157c39", "sfdc": "0015000000WWD2a"},
        {"team": "609b0aa91be27700a4ecd015", "sfdc": "0015000000AbC1z"},
    ]
    result = ids.ordinal_correlation(rows, "team", "sfdc")
    assert result["correlated"] is False


def test_ordinal_correlation_needs_enough_rows():
    rows = [{"team": "66ttx0000000000000000001", "sfdc": "001TTX000000001"}]
    result = ids.ordinal_correlation(rows, "team", "sfdc", min_rows=3)
    assert result["correlated"] is False
    assert result["reason"] == "not enough rows"


# --- Column classification --------------------------------------------------


def test_classify_column_flags_all_invalid_object_ids():
    values = ["66ttx000000000000000027", "66ttx000000000000000024"]
    verdict = ids.classify_column(values, "object_id")
    assert verdict["valid"] == 0
    assert verdict["total"] == 2
    assert verdict["verdict"] == "invalid"


def test_classify_column_passes_real_object_ids():
    values = ["694375d2ea31700011157c39", "609b0aa91be27700a4ecd015"]
    verdict = ids.classify_column(values, "object_id")
    assert verdict["verdict"] == "valid"


def test_classify_column_reports_mixed():
    values = ["694375d2ea31700011157c39", "66ttx000000000000000027"]
    verdict = ids.classify_column(values, "object_id")
    assert verdict["verdict"] == "mixed"


def test_classify_column_rejects_unknown_kind():
    with pytest.raises(ValueError):
        ids.classify_column(["x"], "not-a-kind")

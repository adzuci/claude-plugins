from __future__ import annotations

import pytest

scan = pytest.importorskip("scan_reserved_values")


# --- Reserved domains (RFC 2606 / RFC 6761) ---------------------------------


def test_reserved_tlds_detected():
    assert scan.is_reserved_domain("praxis-systems.example")
    assert scan.is_reserved_domain("host.test")
    assert scan.is_reserved_domain("thing.invalid")
    assert scan.is_reserved_domain("box.localhost")


def test_reserved_second_level_domains_detected():
    assert scan.is_reserved_domain("example.com")
    assert scan.is_reserved_domain("example.net")
    assert scan.is_reserved_domain("example.org")


def test_real_domains_not_flagged():
    assert not scan.is_reserved_domain("apollo.io")
    assert not scan.is_reserved_domain("exampleco.com")
    assert not scan.is_reserved_domain("mytest.com")


def test_domain_check_is_case_insensitive():
    assert scan.is_reserved_domain("Praxis-Systems.EXAMPLE")


def test_email_domain_extraction():
    assert scan.email_domain("luca.costa.00001@praxis-systems.example") == (
        "praxis-systems.example"
    )
    assert scan.email_domain("not-an-email") is None
    assert scan.email_domain("") is None


def test_reserved_email_detected():
    assert scan.is_reserved_email("avery.wren.00003@mail.example")
    assert not scan.is_reserved_email("adam.blackwell@apollo.io")


# --- Fictional phone numbers (NANP 555-0100..555-0199) ----------------------


def test_nanp_fictional_range_detected():
    assert scan.is_fictional_phone("+1 202-555-0100")
    assert scan.is_fictional_phone("+1 202-555-0199")
    assert scan.is_fictional_phone("(202) 555-0137")
    assert scan.is_fictional_phone("2025550100")


def test_555_outside_fictional_range_not_flagged():
    # 555-1212 is real directory assistance; only 0100-0199 is reserved.
    assert not scan.is_fictional_phone("+1 202-555-1212")
    assert not scan.is_fictional_phone("+1 202-555-2938")


def test_ordinary_numbers_not_flagged():
    assert not scan.is_fictional_phone("+1 617-555")
    assert not scan.is_fictional_phone("+44 20 7946 0000")
    assert not scan.is_fictional_phone("")


# --- Documentation IP ranges ------------------------------------------------


def test_documentation_ip_ranges_detected():
    assert scan.is_documentation_ip("192.0.2.14")
    assert scan.is_documentation_ip("198.51.100.7")
    assert scan.is_documentation_ip("203.0.113.255")


def test_real_ips_not_flagged():
    assert not scan.is_documentation_ip("10.0.0.1")
    assert not scan.is_documentation_ip("8.8.8.8")
    assert not scan.is_documentation_ip("not-an-ip")


# --- Whole-sample scan ------------------------------------------------------


def test_scan_rows_counts_reserved_values():
    rows = [
        {
            "work_email": "luca.costa.00001@praxis-systems.example",
            "direct_dial": "+1 202-555-0100",
        },
        {
            "work_email": "luca.voss.00002@praxis-systems.example",
            "direct_dial": "+1 202-555-0137",
        },
    ]
    report = scan.scan_rows(rows)
    assert report["rows"] == 2
    assert report["reserved_emails"] == 2
    assert report["fictional_phones"] == 2
    assert report["verdict"] == "synthetic"


def test_scan_rows_on_clean_data_is_inconclusive_not_genuine():
    # The skill can prove synthetic; it can never prove genuine.
    rows = [{"work_email": "adam.blackwell@apollo.io", "direct_dial": "+1 617 555 1212"}]
    report = scan.scan_rows(rows)
    assert report["reserved_emails"] == 0
    assert report["verdict"] == "inconclusive"
    assert "genuine" not in report["verdict"]


def test_scan_rows_partial_contamination_flags_synthetic():
    rows = [
        {"work_email": "real.person@apollo.io"},
        {"work_email": "fake.person@thing.example"},
    ]
    report = scan.scan_rows(rows)
    assert report["reserved_emails"] == 1
    assert report["verdict"] == "synthetic"


def test_scan_rows_handles_empty_input():
    report = scan.scan_rows([])
    assert report["rows"] == 0
    assert report["verdict"] == "inconclusive"

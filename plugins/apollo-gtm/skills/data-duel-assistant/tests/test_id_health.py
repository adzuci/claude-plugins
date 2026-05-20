import pytest

id_health = pytest.importorskip("id_health")


@pytest.mark.parametrize("value", ["#N/A", "null", "", "  ", "--", None, float("nan")])
def test_is_junk_true(value):
    assert id_health.is_junk(value) is True


@pytest.mark.parametrize("value", ["apollo.io", "Acme Inc", "0"])
def test_is_junk_false(value):
    assert id_health.is_junk(value) is False


@pytest.mark.parametrize("value,expected", [
    ("apollo.io", True),
    ("https://apollo.io/", True),
    ("HTTP://Apollo.IO", True),
    ("gmail.com", False),
    ("nodot", False),
    ("foo.x", False),
    ("", False),
    ("#N/A", False),
])
def test_has_valid_domain(value, expected):
    assert id_health.has_valid_domain(value) is expected


@pytest.mark.parametrize("value,expected", [
    ("https://www.linkedin.com/in/jane", True),
    ("LINKEDIN.COM/company/acme", True),
    ("apollo.io", False),
    ("", False),
])
def test_has_valid_li_url(value, expected):
    assert id_health.has_valid_li_url(value) is expected


def test_has_valid_email_work():
    assert id_health.has_valid_email("jane@apollo.io") == (True, False)


def test_has_valid_email_generic():
    assert id_health.has_valid_email("jane@gmail.com") == (True, True)


def test_has_valid_email_missing():
    assert id_health.has_valid_email("not-an-email") == (False, False)
    assert id_health.has_valid_email("#N/A") == (False, False)


def test_find_col_case_insensitive():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame(columns=["Organization_Website", "Email"])
    assert id_health.find_col(df, ["organization_website", "domain"]) == "Organization_Website"
    assert id_health.find_col(df, ["phone"]) is None

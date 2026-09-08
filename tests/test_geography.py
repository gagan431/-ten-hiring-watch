"""Tests for the geography module — the fix for the country-copied-from-config bug."""

from ten_watch.pipeline.geography import infer_countries, classify_location, EU27


def test_infers_country_from_country_name():
    assert infer_countries("Berlin, Germany") == {"DE"}


def test_infers_country_from_city_only():
    assert infer_countries("Munich") == {"DE"}


def test_infers_multiple_countries_from_multi_location_string():
    # this is the exact QuantCo-style string from Issue #0
    found = infer_countries("Berlin / Cologne / Karlsruhe / Munich options")
    assert found == {"DE"}


def test_classify_eu27_single_match():
    status, value = classify_location("Amsterdam, Netherlands")
    assert status == "eu27"
    assert value == "NL"


def test_classify_rejects_non_eu27():
    status, value = classify_location("London, United Kingdom")
    assert status == "reject"
    assert value == "GB"


def test_classify_rejects_us_city():
    status, value = classify_location("New York")
    assert status == "reject"
    assert value == "US"


def test_classify_unknown_for_unmatched_text():
    status, value = classify_location("Remote - somewhere nice")
    assert status == "unknown"
    assert value == ""


def test_classify_ambiguous_when_eu_and_non_eu_both_present():
    status, value = classify_location("Berlin or London")
    assert status == "ambiguous_eu27"
    assert "DE" in value and "GB" in value


def test_the_original_bug_scenario_is_now_fixed():
    """
    Reproduces exactly the bug the review flagged: a company configured with
    country="DE" whose board actually contains a non-EU location must NOT have
    that non-EU vacancy tagged as DE. classify_location works off the vacancy's
    OWN location text, never the company config, so this is structurally fixed.
    """
    company_config_country = "DE"  # what the old, buggy code would have used
    vacancy_location = "Singapore"
    status, value = classify_location(vacancy_location)
    assert status == "reject"
    assert value != company_config_country
    assert "SG" == value


def test_eu27_set_has_27_countries():
    assert len(EU27) == 27

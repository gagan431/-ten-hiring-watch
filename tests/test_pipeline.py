"""
Tests run WITHOUT hitting real ATS endpoints — `requests.get` is monkeypatched to return
the fixture JSON, so this exercises the actual parsing/flagging/dedupe code, just not
live network calls.
"""

import json
from pathlib import Path

import pytest

from ten_watch.scrapers.greenhouse import fetch_greenhouse_jobs
from ten_watch.scrapers.lever import fetch_lever_jobs
from ten_watch.scrapers.ashby import fetch_ashby_jobs
from ten_watch.pipeline.keyword_flag import flag_keywords, extract_snippet, flag_job
from ten_watch.pipeline.dedupe import dedupe, dedupe_key

FIXTURES = Path(__file__).parent / "fixtures"


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture
def mock_get(monkeypatch):
    def _install(module, fixture_file):
        payload = json.loads((FIXTURES / fixture_file).read_text())
        def fake_get(url, params=None, timeout=None):
            return FakeResponse(payload)
        monkeypatch.setattr(module, "requests", type("M", (), {"get": staticmethod(fake_get), "RequestException": Exception}))
    return _install


def test_greenhouse_parses_fixture_and_unescapes_html(mock_get):
    import ten_watch.scrapers.greenhouse as gh
    mock_get(gh, "greenhouse_sample.json")
    jobs = fetch_greenhouse_jobs("democo")
    assert len(jobs) == 2
    backend = next(j for j in jobs if j["role"] == "Software Engineer, Backend")
    assert "<p>" in backend["description_text"]
    assert "visa sponsorship" in backend["description_text"].lower()


def test_lever_parses_fixture_including_lists_field(mock_get):
    import ten_watch.scrapers.lever as lv
    mock_get(lv, "lever_sample.json")
    jobs = fetch_lever_jobs("democo")
    assert len(jobs) == 2
    fe = next(j for j in jobs if j["role"] == "Senior Frontend Engineer")
    assert "visa sponsorship" in fe["description_text"].lower()


def test_ashby_parses_fixture_and_strips_html(mock_get):
    import ten_watch.scrapers.ashby as ab
    mock_get(ab, "ashby_sample.json")
    jobs = fetch_ashby_jobs("democo")
    assert len(jobs) == 1
    assert "<p>" not in jobs[0]["description_text"]
    assert "poland" in jobs[0]["description_text"].lower()


def test_flag_keywords_finds_relevant_access_phrases():
    text = "Relocation support including visa sponsorship and housing assistance is available."
    matched = flag_keywords(text)
    assert "visa sponsorship" in matched
    assert "relocation support" in matched


@pytest.mark.parametrize("text", [
    "We ensure compliance with Visa, Mastercard and other card-network rules.",
    "Act as the executive sponsor for the strategic programme.",
    "Experience with sports marketing and sponsorship activations is preferred.",
    "Own conference sponsorships and event partnerships across EMEA.",
    "Work with BIN sponsor requirements and payment partners.",
])
def test_flag_keywords_rejects_business_false_positives(text):
    assert flag_keywords(text) == []


@pytest.mark.parametrize("text, expected", [
    ("Visa sponsorship is available for eligible candidates.", "visa sponsorship"),
    ("Do you require sponsorship to work in Germany?", "require sponsorship"),
    ("You must already have the right to work in Ireland.", "right to work"),
    ("Relocation assistance is available for candidates moving to Warsaw.", "relocation assistance"),
    ("Based in or willing to relocate to Madrid, Spain.", "relocate to"),
])
def test_flag_keywords_accepts_candidate_access_language(text, expected):
    assert expected in flag_keywords(text)


def test_flag_keywords_ignores_irrelevant_text():
    assert flag_keywords("Front-desk and office operations role.") == []


def test_extract_snippet_returns_context_around_match():
    text = "Some intro text. Do you require visa sponsorship to work in Germany? More text after."
    snippet = extract_snippet(text, "visa sponsorship", window=60)
    assert "visa sponsorship" in snippet.lower()


def test_dedupe_collapses_identical_company_role_location():
    jobs = [
        {"company": "democo", "role": "Backend Engineer", "city_raw": "Berlin"},
        {"company": "DemoCo", "role": "backend engineer", "city_raw": "berlin"},
        {"company": "democo", "role": "Frontend Engineer", "city_raw": "Berlin"},
    ]
    result = dedupe(jobs)
    assert len(result) == 2


def test_dedupe_key_is_stable_and_case_insensitive():
    k1 = dedupe_key("QuantCo", "Software Engineer", "Berlin")
    k2 = dedupe_key("quantco", "software engineer", "berlin")
    assert k1 == k2


def test_flag_job_end_to_end_on_sponsorship_role():
    job = {"description_text": "We offer visa sponsorship for this role in Munich."}
    flagged = flag_job(job)
    assert "visa sponsorship" in flagged["matched_keywords"]
    assert flagged["evidence_snippet"] != ""


def test_orchestrator_rejects_non_eu_jobs_from_a_global_company_board(monkeypatch):
    import ten_watch.scrapers.greenhouse as gh
    from ten_watch.pipeline.build_review_queue import run

    payload = json.loads((FIXTURES / "greenhouse_mixed_locations.json").read_text())

    def fake_get(url, params=None, timeout=None):
        return FakeResponse(payload)
    monkeypatch.setattr(gh, "requests", type(
        "M", (), {"get": staticmethod(fake_get), "RequestException": Exception}
    ))

    companies = [{"company": "GlobalCo", "ats": "greenhouse", "token": "globalco",
                  "target_countries": ["DE"]}]
    jobs = run(companies)

    assert len(jobs) == 1
    assert jobs[0]["country"] == "DE"
    assert jobs[0]["company"] == "GlobalCo"
    assert "Berlin" in jobs[0]["city_raw"]


def test_orchestrator_routes_unknown_location_out_of_main_review(monkeypatch):
    import ten_watch.pipeline.build_review_queue as brq

    jobs = [
        {
            "role": "Backend Engineer",
            "city_raw": "Berlin, Germany",
            "description_text": "Visa sponsorship is available.",
            "source_ats": "greenhouse",
        },
        {
            "role": "Platform Engineer",
            "city_raw": "Remote",
            "description_text": "Visa sponsorship is available.",
            "source_ats": "greenhouse",
        },
    ]

    monkeypatch.setitem(brq.SCRAPERS, "greenhouse", lambda token: [dict(j) for j in jobs])
    companies = [{"company": "GlobalCo", "ats": "greenhouse", "token": "globalco"}]

    review, unresolved = brq.run_with_unresolved(companies)

    assert len(review) == 1
    assert review[0]["country"] == "DE"
    assert len(unresolved) == 1
    assert unresolved[0]["country"].startswith("UNKNOWN")

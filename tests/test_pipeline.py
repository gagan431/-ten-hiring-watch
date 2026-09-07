"""
Tests run WITHOUT hitting real ATS endpoints — `requests.get` is monkeypatched to return
the fixture JSON, so this exercises the actual parsing/flagging/dedupe code, just not
live network calls. (This build's sandbox couldn't reach boards-api.greenhouse.io etc.
directly — see README for how to smoke-test against the real APIs.)
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
    """Patches requests.get in each scraper module to serve fixture JSON."""
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
    assert "<p>" in backend["description_text"]  # unescaped, not &lt;p&gt;
    assert "visa sponsorship" in backend["description_text"].lower()


def test_lever_parses_fixture_including_lists_field(mock_get):
    import ten_watch.scrapers.lever as lv
    mock_get(lv, "lever_sample.json")
    jobs = fetch_lever_jobs("democo")
    assert len(jobs) == 2
    fe = next(j for j in jobs if j["role"] == "Senior Frontend Engineer")
    # the sponsorship question lives in `lists`, not the main description — must be captured
    assert "visa sponsorship" in fe["description_text"].lower()


def test_ashby_parses_fixture_and_strips_html(mock_get):
    import ten_watch.scrapers.ashby as ab
    mock_get(ab, "ashby_sample.json")
    jobs = fetch_ashby_jobs("democo")
    assert len(jobs) == 1
    assert "<p>" not in jobs[0]["description_text"]
    assert "poland" in jobs[0]["description_text"].lower()


def test_flag_keywords_finds_relevant_terms():
    text = "Relocation support including visa sponsorship and housing assistance is available."
    matched = flag_keywords(text)
    assert "visa" in matched
    assert "sponsorship" in matched
    assert "relocation" in matched


def test_flag_keywords_ignores_irrelevant_text():
    assert flag_keywords("Front-desk and office operations role.") == []


def test_extract_snippet_returns_context_around_match():
    text = "Some intro text. Do you require visa sponsorship to work in Germany? More text after."
    snippet = extract_snippet(text, "visa", window=40)
    assert "visa" in snippet.lower()


def test_dedupe_collapses_identical_company_role_location():
    jobs = [
        {"company": "democo", "role": "Backend Engineer", "city_raw": "Berlin"},
        {"company": "DemoCo", "role": "backend engineer", "city_raw": "berlin"},  # same, different case
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
    assert "visa" in flagged["matched_keywords"]
    assert flagged["evidence_snippet"] != ""

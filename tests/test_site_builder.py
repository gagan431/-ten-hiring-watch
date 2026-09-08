"""Tests for the publication validator, rendering safety, slugs and reality-check logic."""

from pathlib import Path

import ten_watch.site.build_site as site_builder
from ten_watch.site.build_site import (
    build,
    select_reality_check,
    slugify,
    vacancy_slug,
    validate_for_publish,
)
from ten_watch.schema import REVIEW_CSV_COLUMNS


def _row(**overrides):
    row = {c: "" for c in REVIEW_CSV_COLUMNS}
    row.update(
        tier="A",
        original_vacancy_url="https://x.com/1",
        source_quality="P1",
        evidence_confidence="Verified",
        re_verification_date="2026-09-08",
        is_open="True",
        publish_decision="yes",
        access_mechanism="Employer-sponsored work visa",
    )
    row.update(overrides)
    return row


def test_complete_a_tier_row_passes():
    assert validate_for_publish(_row()) == []


def test_a_tier_without_access_mechanism_fails_gate_8():
    errors = validate_for_publish(_row(access_mechanism=""))
    assert any("Gate 8" in e for e in errors)


def test_b_tier_without_access_mechanism_is_fine():
    assert validate_for_publish(_row(tier="B", evidence_confidence="Indicated", access_mechanism="")) == []


def test_missing_source_url_fails():
    errors = validate_for_publish(_row(tier="C", original_vacancy_url="", source_quality="P2", evidence_confidence="Unclear", access_mechanism=""))
    assert any("source URL" in e for e in errors)


def test_stale_row_fails_gate_1():
    errors = validate_for_publish(_row(is_open="False"))
    assert any("Gate 1" in e for e in errors)


def test_blank_liveness_fails_closed_gate_1():
    errors = validate_for_publish(_row(is_open=""))
    assert any("positively confirmed live" in e for e in errors)


def test_invalid_source_quality_fails():
    errors = validate_for_publish(_row(source_quality="banana"))
    assert any("P1/P2/P3" in e for e in errors)


def test_invalid_evidence_confidence_fails():
    errors = validate_for_publish(_row(evidence_confidence="whatever"))
    assert any("Verified/Indicated/Unclear/Restricted" in e for e in errors)


def test_missing_human_publish_decision_fails_gates_3_4_7():
    errors = validate_for_publish(_row(publish_decision=""))
    assert any("Gates 3/4/7" in e for e in errors)


def test_explicit_no_publish_decision_fails_gates_3_4_7():
    errors = validate_for_publish(_row(publish_decision="no"))
    assert any("Gates 3/4/7" in e for e in errors)


def test_invalid_tier_fails_immediately():
    assert validate_for_publish(_row(tier="Q")) == ["tier missing or invalid"]


def test_slugify_produces_url_safe_lowercase():
    assert slugify("QuantCo", "Software Engineer", "Berlin") == "quantco-software-engineer-berlin"


def test_vacancy_slug_appends_short_hash_for_uniqueness():
    row = {"company": "QuantCo", "role": "Software Engineer", "city": "Berlin", "dedupe_hash": "d77074bb3dc457f0"}
    slug = vacancy_slug(row)
    assert slug.startswith("quantco-software-engineer-berlin-")
    assert slug.endswith("d77074")


def test_reality_check_uses_human_flag_when_present():
    rows = [
        {"tier": "D", "reality_check_candidate": "no", "company": "A", "role": "X"},
        {"tier": "B", "reality_check_candidate": "yes", "company": "B", "role": "Y"},
    ]
    result = select_reality_check(rows)
    assert len(result) == 1
    assert result[0]["company"] == "B"


def test_reality_check_falls_back_to_d_tier_when_nothing_flagged():
    rows = [
        {"tier": "D", "reality_check_candidate": "", "company": "A", "role": "X"},
        {"tier": "A", "reality_check_candidate": "", "company": "B", "role": "Y"},
    ]
    result = select_reality_check(rows)
    assert len(result) == 1
    assert result[0]["company"] == "A"


def test_jinja_autoescapes_untrusted_vacancy_fields(tmp_path, monkeypatch):
    csv_path = tmp_path / "queue-2026-09-08-classified.csv"
    row = _row(
        company="GlobalCo",
        role="<script>alert(1)</script>",
        country="DE",
        city="Berlin",
        source_ats="greenhouse",
        evidence_snippet='<img src=x onerror=alert(2)>',
        dedupe_hash="abcdef123456",
    )
    import csv
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REVIEW_CSV_COLUMNS)
        w.writeheader()
        w.writerow(row)

    out = tmp_path / "output"
    monkeypatch.setattr(site_builder, "OUTPUT_DIR", out)
    build(str(csv_path), issue_date="2026-09-08")

    vacancy_html = next((out / "vacancies").glob("*/index.html")).read_text(encoding="utf-8")
    assert "<script>alert(1)</script>" not in vacancy_html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in vacancy_html
    assert '<img src=x onerror=alert(2)>' not in vacancy_html
    assert "&lt;img src=x onerror=alert(2)&gt;" in vacancy_html


def test_build_generates_public_access_terminology_page(tmp_path, monkeypatch):
    csv_path = tmp_path / "queue-2026-09-08-classified.csv"
    row = _row(company="GlobalCo", role="Engineer", country="DE", city="Berlin", source_ats="greenhouse", evidence_snippet="Visa sponsorship available", dedupe_hash="abcdef123456")
    import csv
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REVIEW_CSV_COLUMNS)
        w.writeheader()
        w.writerow(row)

    out = tmp_path / "output"
    monkeypatch.setattr(site_builder, "OUTPUT_DIR", out)
    build(str(csv_path), issue_date="2026-09-08")

    glossary = out / "access-mechanisms" / "index.html"
    assert glossary.exists()
    text = glossary.read_text(encoding="utf-8")
    assert "under specialist review" in text
    assert "They are not immigration advice" in text

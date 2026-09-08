"""
Site builder — Part IV: "one evergreen page per issue... a static, indexable page per
vacancy with its evidence quote and tier, so search traffic can land on individual
verified roles even between newsletter sends."

Input: a review CSV that a HUMAN has already filled in (tier, access_mechanism,
profession, editorial_note, etc.). This script does not classify anything — it only
renders whatever a person already decided, AND it enforces that the decision is
actually complete before anything ships (Gates 1-8, Part II.5). A row missing a
required field fails the whole build rather than publishing silently with a
placeholder — an earlier version of this script quietly substituted
"Unspecified — verify directly" for a missing A-tier access mechanism, which is
exactly the kind of silent guess the operating model exists to prevent.

Output: site/output/
  index.html                        — the issue in the canonical v2 structure (Part II.9)
  vacancies/{slug}/index.html        — one evergreen page per classified vacancy,
                                       with <title>/meta description/canonical/og tags

Run: python -m ten_watch.site.build_site review/queue-2026-09-07-classified.csv
"""

import csv
import os
import re
import sys
from pathlib import Path

from jinja2 import Environment, select_autoescape

TIER_LABELS = {
    "A": "🟢 STRONG INTERNATIONAL-ACCESS OPPORTUNITIES",
    "B": "🟡 WORTH INVESTIGATING",
    "C": "🟠 VERIFY BEFORE INVESTING TIME",
    "D": "🔴 RESTRICTIONS TO NOTICE",
}

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "site" / "output"

# Canonical base URL is environment-driven so local/staging/production builds
# cannot accidentally ship a placeholder domain. GitHub Actions supplies the
# real repository Pages URL at build time; custom domains can override it with
# the SITE_BASE_URL repository variable.
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "http://localhost").rstrip("/")

VALID_SOURCE_QUALITIES = {"P1", "P2", "P3"}
VALID_EVIDENCE_CONFIDENCE = {"Verified", "Indicated", "Unclear", "Restricted"}

ENV = Environment(autoescape=select_autoescape(["html", "xml"]))


# ---------------------------------------------------------------------------
# Gate enforcement (Part II.5) — the piece the previous version was missing.
# ---------------------------------------------------------------------------

def validate_for_publish(row: dict) -> list[str]:
    """Returns a list of gate-failure reasons; empty list = publishable."""
    errors = []

    if row.get("tier") not in TIER_LABELS:
        errors.append("tier missing or invalid")
        return errors  # nothing else is meaningful to check without a valid tier

    if not row.get("original_vacancy_url"):
        errors.append("source URL missing (Gate 2 — Original)")
    if row.get("source_quality") not in VALID_SOURCE_QUALITIES:
        errors.append("source quality must be one of P1/P2/P3 (Gate 2 — Original)")
    if row.get("evidence_confidence") not in VALID_EVIDENCE_CONFIDENCE:
        errors.append("evidence confidence must be Verified/Indicated/Unclear/Restricted (Gate 5 — Evidence)")
    if not row.get("re_verification_date"):
        errors.append("re-verification date missing (Gate 6 — Fresh enough)")
    if row.get("is_open") != "True":
        errors.append("vacancy is not positively confirmed live (Gate 1 — Live)")
    if (row.get("publish_decision") or "").strip().lower() != "yes":
        errors.append("human editorial approval missing (Gates 3/4/7 — Distinct/Relevant/Useful)")
    if row["tier"] == "A" and not row.get("access_mechanism"):
        errors.append("A-tier access mechanism unresolved (Gate 8)")

    return errors


def load_and_validate(csv_path: Path) -> tuple[list[dict], dict[str, list[str]]]:
    """Returns (publishable_rows, {row_label: [errors]} for anything that failed)."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # rows with no tier at all were simply never reached in review — not an error,
    # just not ready yet. Only rows with SOME tier set go through full validation,
    # so an in-progress queue doesn't spam failures for rows nobody's looked at.
    attempted = [r for r in rows if r.get("tier")]

    publishable, failed = [], {}
    for row in attempted:
        errors = validate_for_publish(row)
        label = f"{row.get('company','?')} — {row.get('role','?')}"
        if errors:
            failed[label] = errors
        else:
            publishable.append(row)
    return publishable, failed


# ---------------------------------------------------------------------------
# Slugs
# ---------------------------------------------------------------------------

def slugify(*parts: str) -> str:
    text = "-".join(p for p in parts if p).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def vacancy_slug(row: dict) -> str:
    base = slugify(row.get("company", ""), row.get("role", ""), row.get("city", ""))
    short_hash = (row.get("dedupe_hash") or "")[:6]
    return f"{base}-{short_hash}" if short_hash else base


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

BASE_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{{ title }}</title>
<meta name="description" content="{{ description }}">
<link rel="canonical" href="{{ canonical_url }}">
<meta property="og:title" content="{{ title }}">
<meta property="og:description" content="{{ description }}">
<meta property="og:url" content="{{ canonical_url }}">
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
"""
BASE_FOOT = "</body>\n</html>\n"

VACANCY_TEMPLATE = ENV.from_string(BASE_HEAD + """
<article>
  <h1>{{ row.role }} — {{ row.company }}</h1>
  <p><strong>Country:</strong> {{ row.country }}<br>
     <strong>City:</strong> {{ row.city }}<br>
     <strong>Tier:</strong> {{ tier_label }}<br>
     <strong>Access mechanism:</strong> {{ row.access_mechanism or "Unspecified — verify directly" }}<br>
     <strong>Source:</strong> {{ row.source_ats }} (P-quality: {{ row.source_quality }})<br>
     <strong>Evidence confidence:</strong> {{ row.evidence_confidence }}<br>
     <strong>Re-verified:</strong> {{ row.re_verification_date }}</p>

  <h2>Evidence</h2>
  <blockquote>{{ row.evidence_snippet }}</blockquote>

  {% if row.editorial_note %}
  <h2>TEN note</h2>
  <p>{{ row.editorial_note }}</p>
  {% endif %}

  <p><a href="{{ row.original_vacancy_url }}">Original vacancy</a></p>
</article>
""" + BASE_FOOT)

INDEX_TEMPLATE = ENV.from_string(BASE_HEAD + """
<h1>TEN International Hiring Watch — EU27</h1>
<p>Issue | {{ issue_date }}</p>

<h2>🔍 This Week's Reality Check</h2>
<ul>
{% for r in reality_check_rows %}
  <li><strong>{{ r.company }} — {{ r.role }}:</strong> {{ r.evidence_snippet }}</li>
{% endfor %}
</ul>

{% for tier, label in tier_labels.items() %}
  {% if grouped[tier] %}
  <h2>{{ label }}</h2>
  <ul>
  {% for r in grouped[tier] %}
    <li><a href="vacancies/{{ r.slug }}/">{{ r.company }} — {{ r.role }}</a> ({{ r.country }})</li>
  {% endfor %}
  </ul>
  {% endif %}
{% endfor %}

<h2>About This Watch</h2>
<p>Evidence methodology: original ATS/employer evidence only, A/B/C/D confidence tiers,
no sponsorship-probability scoring. Every source in this issue is an English-language ATS
or careers page — a known bias, not a neutral sample. See the
<a href="access-mechanisms/">access-mechanism glossary</a>.</p>
""" + BASE_FOOT)


PUBLIC_GLOSSARY_TEMPLATE = ENV.from_string(BASE_HEAD + """
<main>
  <h1>International-access terminology</h1>
  <p>This page is intentionally conservative while TEN's detailed immigration-law glossary is under specialist review.</p>
  <h2>What the Hiring Watch labels mean</h2>
  <ul>
    <li><strong>A — Explicit international support:</strong> the vacancy or applicable employer evidence explicitly confirms visa/work-permit or immigration support.</li>
    <li><strong>B — International route indicated:</strong> sponsorship-dependent or relocating applicants are explicitly contemplated, but employer support is not confirmed.</li>
    <li><strong>C — Mobility signal only:</strong> relocation or international-working signals exist without sufficient work-authorisation evidence.</li>
    <li><strong>D — Restricted:</strong> the vacancy explicitly requires existing work rights or says sponsorship is unavailable.</li>
  </ul>
  <p>These labels describe the evidence in a vacancy. They are not immigration advice and do not predict whether an individual applicant will receive a visa or work permit.</p>
</main>
""" + BASE_FOOT)

# ---------------------------------------------------------------------------
# Reality-check selection — Part II.9. Fixed per review: the earlier version's
# variable was literally named d_and_sharp_b but only ever selected D-tier.
# Now driven by a HUMAN-set flag (reality_check_candidate), never an algorithmic
# guess at which B-tier catch is "sharp".
# ---------------------------------------------------------------------------

def select_reality_check(rows: list[dict]) -> list[dict]:
    flagged = [r for r in rows if (r.get("reality_check_candidate") or "").strip().lower() == "yes"]
    if flagged:
        return flagged
    # fallback only: no human flagged anything, default to D-tier per the documented
    # default lead — but this is a fallback, not the primary mechanism.
    return [r for r in rows if r.get("tier") == "D"][:2]


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build(csv_path: str, issue_date: str = ""):
    csv_path = Path(csv_path)
    publishable, failed = load_and_validate(csv_path)

    if failed:
        print(f"BUILD FAILED — {len(failed)} row(s) did not pass the publication gates:\n")
        for label, errors in failed.items():
            print(f"  {label}:")
            for e in errors:
                print(f"    - {e}")
        print("\nFix these in the CSV (or move them back out of review) and re-run. "
              "Nothing was published.")
        sys.exit(1)

    if not publishable:
        print(f"No publishable (tier-filled, gate-passing) rows found in {csv_path} — nothing to build.")
        return

    for r in publishable:
        r["slug"] = vacancy_slug(r)

    issue_date = issue_date or csv_path.stem.replace("queue-", "").replace("-classified", "")

    vac_root = OUTPUT_DIR / "vacancies"
    for r in publishable:
        page_dir = vac_root / r["slug"]
        page_dir.mkdir(parents=True, exist_ok=True)
        title = f"{r['role']} at {r['company']} — TEN International Hiring Watch"
        description = (r.get("evidence_snippet") or "")[:155]
        html = VACANCY_TEMPLATE.render(
            title=title,
            description=description,
            canonical_url=f"{SITE_BASE_URL}/vacancies/{r['slug']}/",
            row=r,
            tier_label=TIER_LABELS.get(r["tier"], r["tier"]),
        )
        (page_dir / "index.html").write_text(html, encoding="utf-8")

    grouped = {t: [r for r in publishable if r["tier"] == t] for t in TIER_LABELS}
    index_html = INDEX_TEMPLATE.render(
        title=f"TEN International Hiring Watch — EU27 | {issue_date}",
        description="Verified EU27 international-access job vacancies, evidence-tiered A-D.",
        canonical_url=f"{SITE_BASE_URL}/",
        issue_date=issue_date,
        reality_check_rows=select_reality_check(publishable),
        grouped=grouped,
        tier_labels=TIER_LABELS,
    )
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "index.html").write_text(index_html, encoding="utf-8")

    glossary_dir = OUTPUT_DIR / "access-mechanisms"
    glossary_dir.mkdir(parents=True, exist_ok=True)
    glossary_html = PUBLIC_GLOSSARY_TEMPLATE.render(
        title="International-access terminology — TEN International Hiring Watch",
        description="How TEN interprets international-access evidence in European vacancies.",
        canonical_url=f"{SITE_BASE_URL}/access-mechanisms/",
    )
    (glossary_dir / "index.html").write_text(glossary_html, encoding="utf-8")

    print(f"Built {len(publishable)} vacancy pages + index.html + access terminology page into {OUTPUT_DIR}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m ten_watch.site.build_site <classified_review.csv>")
        sys.exit(1)
    build(sys.argv[1])

"""
Orchestrator for Part VI, Phase 1.

Reads config/companies.yaml -> scrapes each company's ATS -> infers each vacancy's
OWN country from its location text (not the company's config) -> drops non-EU27
vacancies, flags unresolved ones instead of dropping them -> flags keyword hits ->
dedupes -> writes review/queue-{date}.csv with the AUTOMATED schema fields filled in
and every HUMAN field (tier, access_mechanism, profession, editorial_note...) left
blank for a person to fill in, per the review workflow in README.md.

Run: python -m ten_watch.pipeline.build_review_queue
"""

import csv
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # allow running as a script too

from ten_watch.scrapers.greenhouse import fetch_greenhouse_jobs
from ten_watch.scrapers.lever import fetch_lever_jobs
from ten_watch.scrapers.ashby import fetch_ashby_jobs
from ten_watch.pipeline.keyword_flag import flag_job
from ten_watch.pipeline.dedupe import dedupe
from ten_watch.pipeline.geography import classify_location
from ten_watch.schema import VacancyRecord, REVIEW_CSV_COLUMNS

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

SCRAPERS = {
    "greenhouse": fetch_greenhouse_jobs,
    "lever": fetch_lever_jobs,
    "ashby": fetch_ashby_jobs,
}

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPANIES_FILE = REPO_ROOT / "config" / "companies.yaml"
REVIEW_DIR = REPO_ROOT / "review"


def load_companies(path: Path = COMPANIES_FILE) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg.get("companies", [])


def _process_company(entry: dict, today: str) -> tuple[list[dict], dict]:
    """Fetch one company's board, resolve each job's real country, apply Gate-level
    EU27 filtering. Returns (kept_jobs, stats) — stats logged by the caller."""
    ats = entry.get("ats")
    token = entry.get("token")
    display_name = entry.get("company", token)
    fetch_fn = SCRAPERS.get(ats)

    if fetch_fn is None:
        logger.warning(
            "Skipping %s: unsupported/unimplemented ATS '%s' "
            "(Workday/SmartRecruiters are stubs, see README).", token, ats,
        )
        return [], {"fetched": 0, "rejected_non_eu": 0, "unknown": 0, "kept": 0}

    logger.info("Fetching %s (%s)...", display_name, ats)
    raw_jobs = fetch_fn(token)

    kept = []
    stats = {"fetched": len(raw_jobs), "rejected_non_eu": 0, "unknown": 0, "kept": 0}

    for job in raw_jobs:
        job["ats_token"] = token
        job["company"] = display_name  # human-configured name, not the raw ATS token

        status, country_value = classify_location(job.get("city_raw", ""))
        if status == "reject":
            stats["rejected_non_eu"] += 1
            continue
        elif status == "unknown":
            job["country"] = "UNKNOWN — verify manually"
            stats["unknown"] += 1
        elif status == "ambiguous_eu27":
            job["country"] = f"MULTIPLE ({country_value}) — verify location"
            stats["kept"] += 1
        else:  # "eu27"
            job["country"] = country_value
            stats["kept"] += 1

        job["first_verified_date"] = today
        job["re_verification_date"] = today
        kept.append(job)

    return kept, stats


def run(companies: list[dict] | None = None) -> list[dict]:
    companies = companies if companies is not None else load_companies()
    today = date.today().isoformat()
    all_jobs: list[dict] = []

    for entry in companies:
        kept, stats = _process_company(entry, today)
        logger.info(
            "  %d fetched -> %d rejected (non-EU27), %d unknown-location (kept, flagged), %d kept",
            stats["fetched"], stats["rejected_non_eu"], stats["unknown"], stats["kept"],
        )
        for job in kept:
            job = flag_job(job)
        # DISCOVERY filter — only jobs with at least one sponsorship-adjacent keyword hit
        # reach the review queue at all (Part VI). Everything else never burdens a human.
        flagged = [j for j in kept if j.get("matched_keywords")]
        logger.info("  %d of those had a keyword match", len(flagged))
        all_jobs.extend(flagged)

    deduped = dedupe(all_jobs)
    logger.info("Total after dedupe: %d candidate vacancies for human review", len(deduped))
    return deduped


def to_records(jobs: list[dict]) -> list[VacancyRecord]:
    records = []
    for j in jobs:
        records.append(VacancyRecord(
            company=j.get("company", ""),
            role=j.get("role", ""),
            country=j.get("country", ""),
            source_ats=j.get("source_ats", ""),
            ats_token=j.get("ats_token"),
            original_vacancy_url=j.get("original_vacancy_url", ""),
            city=j.get("city_raw"),
            date_posted=j.get("date_posted"),
            raw_id=j.get("raw_id"),
            matched_keywords=j.get("matched_keywords", []),
            evidence_snippet=j.get("evidence_snippet"),
            dedupe_hash=j.get("dedupe_hash"),
            first_verified_date=j.get("first_verified_date"),
            re_verification_date=j.get("re_verification_date"),
        ))
    return records


def write_review_csv(records: list[VacancyRecord], out_dir: Path = REVIEW_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = out_dir / f"queue-{ts}.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_CSV_COLUMNS)
        writer.writeheader()
        for r in records:
            row = r.to_dict()
            row["matched_keywords"] = "; ".join(row.get("matched_keywords") or [])
            writer.writerow(row)
    logger.info("Wrote review queue: %s (%d rows)", out_path, len(records))
    return out_path


def main():
    jobs = run()
    records = to_records(jobs)
    write_review_csv(records)


if __name__ == "__main__":
    main()

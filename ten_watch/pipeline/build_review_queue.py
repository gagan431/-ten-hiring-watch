"""
Orchestrator for Part VI, Phase 1.

Reads config/companies.yaml -> scrapes each company's ATS -> flags keyword hits ->
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


def run(companies: list[dict] | None = None) -> list[dict]:
    companies = companies if companies is not None else load_companies()
    today = date.today().isoformat()
    all_jobs: list[dict] = []

    for entry in companies:
        ats = entry.get("ats")
        token = entry.get("token")
        country = entry.get("country", "")
        fetch_fn = SCRAPERS.get(ats)
        if fetch_fn is None:
            logger.warning("Skipping %s: unsupported/unimplemented ATS '%s' "
                            "(Workday/SmartRecruiters are stubs, see README).", token, ats)
            continue

        logger.info("Fetching %s (%s)...", token, ats)
        jobs = fetch_fn(token)
        for job in jobs:
            job["country"] = country
            job = flag_job(job)
            job["first_verified_date"] = today
            job["re_verification_date"] = today
        # only keep jobs where at least one keyword hit — this is a DISCOVERY filter,
        # per Part VI: undiscussed roles never reach the review queue at all, so a
        # human never has to manually skim postings with zero sponsorship-adjacent language.
        flagged = [j for j in jobs if j.get("matched_keywords")]
        logger.info("  %d jobs fetched, %d keyword-flagged", len(jobs), len(flagged))
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

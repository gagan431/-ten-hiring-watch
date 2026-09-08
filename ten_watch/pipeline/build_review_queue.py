"""
Orchestrator for Part VI, Phase 1.

Reads config/companies.yaml -> scrapes each company's ATS -> infers each vacancy's
OWN country from its location text -> drops non-EU27 vacancies -> routes unresolved
geography into a separate queue -> flags access-phrase hits -> dedupes -> writes the
EU27 human review queue plus a location-resolution queue.

Run: python -m ten_watch.pipeline.build_review_queue
"""

import csv
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

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
    """Fetch one company board and attach per-vacancy geography status.

    Non-EU27 roles are rejected immediately. EU27, ambiguous-EU27 and unknown roles are
    returned so the caller can phrase-filter them before deciding which queue receives them.
    """
    ats = entry.get("ats")
    token = entry.get("token")
    display_name = entry.get("company", token)
    fetch_fn = SCRAPERS.get(ats)

    if fetch_fn is None:
        logger.warning(
            "Skipping %s: unsupported/unimplemented ATS '%s' "
            "(Workday/SmartRecruiters are stubs, see README).", token, ats,
        )
        return [], {"fetched": 0, "rejected_non_eu": 0, "unknown": 0, "ambiguous": 0, "eu27": 0}

    logger.info("Fetching %s (%s)...", display_name, ats)
    raw_jobs = fetch_fn(token)

    candidates = []
    stats = {
        "fetched": len(raw_jobs),
        "rejected_non_eu": 0,
        "unknown": 0,
        "ambiguous": 0,
        "eu27": 0,
    }

    for job in raw_jobs:
        job["ats_token"] = token
        job["company"] = display_name

        status, country_value = classify_location(job.get("city_raw", ""))
        job["location_status"] = status

        if status == "reject":
            stats["rejected_non_eu"] += 1
            continue
        if status == "unknown":
            job["country"] = "UNKNOWN — verify manually"
            stats["unknown"] += 1
        elif status == "ambiguous_eu27":
            job["country"] = f"MULTIPLE ({country_value}) — verify location"
            stats["ambiguous"] += 1
        else:
            job["country"] = country_value
            stats["eu27"] += 1

        job["first_verified_date"] = today
        job["re_verification_date"] = today
        candidates.append(job)

    return candidates, stats


def run_with_unresolved(companies: list[dict] | None = None) -> tuple[list[dict], list[dict]]:
    """Return (confirmed_eu27_review_candidates, unresolved_location_candidates)."""
    companies = companies if companies is not None else load_companies()
    today = date.today().isoformat()
    review_jobs: list[dict] = []
    unresolved_jobs: list[dict] = []

    for entry in companies:
        candidates, stats = _process_company(entry, today)
        logger.info(
            "  %d fetched -> %d rejected (non-EU27), %d unknown, %d ambiguous-EU27, %d confirmed EU27",
            stats["fetched"], stats["rejected_non_eu"], stats["unknown"],
            stats["ambiguous"], stats["eu27"],
        )

        flagged = []
        for job in candidates:
            job = flag_job(job)
            if job.get("matched_keywords"):
                flagged.append(job)

        confirmed = [j for j in flagged if j.get("location_status") == "eu27"]
        unresolved = [j for j in flagged if j.get("location_status") in {"unknown", "ambiguous_eu27"}]

        logger.info(
            "  %d access-phrase matches -> %d EU27 review, %d unresolved-location",
            len(flagged), len(confirmed), len(unresolved),
        )
        review_jobs.extend(confirmed)
        unresolved_jobs.extend(unresolved)

    review_deduped = dedupe(review_jobs)
    unresolved_deduped = dedupe(unresolved_jobs)
    logger.info("Total after dedupe: %d confirmed-EU27 vacancies for human review", len(review_deduped))
    logger.info("Total after dedupe: %d unresolved-location vacancies", len(unresolved_deduped))
    return review_deduped, unresolved_deduped


def run(companies: list[dict] | None = None) -> list[dict]:
    """Backward-compatible entry point returning only confirmed-EU27 review candidates."""
    review_jobs, _ = run_with_unresolved(companies)
    return review_jobs


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


def _write_csv(records: list[VacancyRecord], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_CSV_COLUMNS)
        writer.writeheader()
        for r in records:
            row = r.to_dict()
            row["matched_keywords"] = "; ".join(row.get("matched_keywords") or [])
            writer.writerow(row)
    logger.info("Wrote queue: %s (%d rows)", out_path, len(records))
    return out_path


def write_review_csv(records: list[VacancyRecord], out_dir: Path = REVIEW_DIR) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return _write_csv(records, out_dir / f"queue-{ts}.csv")


def write_unresolved_csv(records: list[VacancyRecord], out_dir: Path = REVIEW_DIR) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return _write_csv(records, out_dir / f"location-resolution-{ts}.csv")


def main():
    review_jobs, unresolved_jobs = run_with_unresolved()
    write_review_csv(to_records(review_jobs))
    write_unresolved_csv(to_records(unresolved_jobs))


if __name__ == "__main__":
    main()

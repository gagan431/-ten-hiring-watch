"""
Dedupe stage — Part VI, Phase 1: "auto-dedupe by company+title+location hash before
a human ever sees it."

Note this is NOT the same as the Part II.8 editorial dedup rule (max one listing per
employer per issue unless seniority differs materially). That rule requires reading
the roles, which is a human editorial call. This stage only removes exact repeats
(the same posting mirrored across offices, or picked up twice in one run) so the
review queue isn't cluttered with literal duplicates before a human applies judgment.
"""

import hashlib


def dedupe_key(company: str, role: str, city: str | None) -> str:
    raw = f"{(company or '').strip().lower()}|{(role or '').strip().lower()}|{(city or '').strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def dedupe(jobs: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for job in jobs:
        key = dedupe_key(job.get("company"), job.get("role"), job.get("city_raw"))
        job["dedupe_hash"] = key
        if key not in seen:
            seen[key] = job
    return list(seen.values())
